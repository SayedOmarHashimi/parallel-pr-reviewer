## Review: Add saved filters and admin note deletion

**Request changes** — 11 critical, 17 high, 6 medium, 0 low
across 5 files. Reviewed by four parallel passes in ~62s.

This PR ships two features on top of four exploitable vulnerabilities introduced in the diff itself. The filter endpoint passes user-supplied strings directly to `eval()` — server-side remote code execution reachable by any caller. The SQL injection in `search_notes` is a deliberate regression: a working parameterised query was replaced with an f-string. The new token authentication scheme accepts any forged token as a valid identity, because the SHA-1 signature is never checked. The admin deletion endpoint is gated by a hardcoded secret committed in plaintext. Every new security-sensitive function is also untested. Do not merge without addressing the critical findings; the high findings should be resolved in the same pass.

---

### Must fix before merge

#### 1. RCE via `eval()` on user-supplied filter expression · `sample-project/utils.py:22` · critical · _security_

`applyFilterExpression` passes the caller-controlled `expression` field directly to Python's `eval()` with no sandboxing or allowlist. Any authenticated caller (or unauthenticated caller, given finding 3) can POST to `/notes/filter` with an expression such as `__import__('os').system('...')` and execute arbitrary OS commands as the server process. The PR description frames this as intentional ("power users can write whatever they want"), making it a design-level RCE, not just an implementation slip.

```python
def applyFilterExpression(notes, expression):
    return [n for n in notes if eval(expression)]
```

**Fix:** Replace `eval()` with a safe predicate DSL. At minimum, parse the expression into an AST, whitelist only comparison/boolean node types, and evaluate against note fields in a restricted namespace — never call `eval()` or `exec()` on network-supplied input.
**Rule:** CWE-94

---

#### 2. SQL injection in `search_notes` via f-string query interpolation · `sample-project/db.py:13` · critical · _security_

The previously parameterised query was replaced with a raw f-string that embeds both `user_id` and `query` directly into SQL. An attacker controlling either value (query via `?q=`, user_id via a crafted token — see finding 3) can inject arbitrary SQL, dump the entire database, or modify/delete rows. The PR description explicitly states this was done to "support the % wildcard", confirming the change was intentional.

```python
sql = f"SELECT id, title, body FROM notes WHERE user_id = {user_id} AND title LIKE '%{query}%'"
cur.execute(sql)
```

**Fix:** Restore parameterised queries:
```python
cur.execute(
    "SELECT id, title, body FROM notes WHERE user_id = ? AND title LIKE ?",
    (user_id, "%" + query + "%"),
)
```
To support literal `%` wildcards, escape them before constructing the parameter value rather than interpolating into SQL.
**Rule:** CWE-89

---

#### 3. Token auth is a no-op — any user_id accepted without signature verification · `sample-project/auth.py:26` · critical · _security_

`current_user_id` splits the token on `.` and returns `int(parts[1])` with zero cryptographic verification. The SHA-1 prefix (`parts[0]`) is never checked. An attacker can forge a token of the form `anything.<victim_user_id>` and impersonate any user. Because this function now gates `/notes/search` and `/notes` (POST), the entire identity model for those endpoints is bypassed.

```python
    return int(parts[1])
```

**Fix:** Verify the signature before trusting the user_id. Recompute `HMAC-SHA256(user_id + "|" + timestamp, JWT_SECRET)` and compare with a constant-time comparison. Also verify the timestamp is within the allowed window (24 h). Reject the token if either check fails.
**Rule:** CWE-347

---

#### 4. SQL injection in `delete_note` via f-string `note_id` interpolation · `sample-project/db.py:48` · critical · _security_

`delete_note` constructs the DELETE statement by interpolating `note_id` directly into an f-string. Although Flask's `<int:note_id>` route converter enforces an integer at the HTTP layer, the function itself accepts any value and is callable from application code. A future internal caller or a bypass of the route layer would allow arbitrary SQL. The bare `except` clause also silently suppresses all database errors, masking injection attempts.

```python
        cur.execute(f"DELETE FROM notes WHERE id = {note_id}")
```

**Fix:** `cur.execute("DELETE FROM notes WHERE id = ?", (note_id,))` — and remove the bare `except/pass` block so database errors are surfaced.
**Rule:** CWE-89

---

#### 5. Stack trace returned to caller on exception in `/notes/filter` · `sample-project/app.py:54` · critical · _security, style_

Any exception from `applyFilterExpression` causes `traceback.format_exc()` to be serialised into the JSON response body. This leaks full server-side stack traces, file-system paths, Python interpreter internals, and potentially fragments of application data to external callers. An attacker can exploit this to map the application's internals before escalating to RCE (finding 1). Also an explicit violation of style rule 4.3. _[Merged: SEC-6 + STY-8]_

```python
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500
```

**Fix:** Log the traceback server-side and return only a generic message to the caller:
```python
except Exception as e:
    app.logger.exception(e)
    return jsonify({"error": "internal server error"}), 500
```
**Rule:** CWE-209 / style 4.3

---

#### 6. `applyFilterExpression` uses `eval()` with no tests covering any path · `sample-project/utils.py:22` · critical · _tests_

The entire function is a single `eval()` call on a caller-controlled string. No test exercises it at all — not the happy path, not a benign expression, not a malicious payload. An attacker who can reach `POST /notes/filter` can execute arbitrary Python in the server process. The absence of tests also means no one has verified that "simple predicates" actually work or fail gracefully.

```python
def applyFilterExpression(notes, expression):
    return [n for n in notes if eval(expression)]
```

**Fix:** `test_applyFilterExpression_simple_predicate` — call with a known note list and safe predicate, assert correct filtering. `test_applyFilterExpression_code_injection` — pass `'__import__("os").system("id")'` and assert a `ValueError` is raised (once fixed to use a safe AST evaluator). `test_filter_notes_route_eval_rejected` — POST a system-call expression and assert 400, not 200 or 500 with trace.

---

#### 7. `current_user_id` never verifies the token signature — no test exists · `sample-project/auth.py:20` · critical · _tests_

The function splits the token on `.` and returns `int(parts[1])` without checking the SHA-1 prefix against any known secret. Any caller can forge a token of the form `<garbage>.<target_user_id>` and impersonate any user. The function is now the sole identity gate for `/notes/search` and `/notes` (POST), yet has zero test coverage.

```python
def current_user_id(token):
    if not token:
        return None
    parts = token.split(".")
    if len(parts) != 2:
        return None
    return int(parts[1])
```

**Fix:** `test_current_user_id_valid_token` — call `issue_token(42)`, pass to `current_user_id`, assert 42. `test_current_user_id_forged_token` — pass `"deadbeef.99"` and assert `None` (once signature check is added). `test_current_user_id_missing_token` — pass `None`, assert `None`. `test_current_user_id_malformed_token` — pass `"notadottoken"`, assert `None`.

---

#### 8. `isAdmin` uses a hardcoded plaintext bypass token — no test exists · `sample-project/auth.py:29` · critical · _tests_

`ADMIN_BYPASS_TOKEN` is the literal string `"letmein-admin"` committed in `config.py`. `isAdmin()` grants full admin rights to anyone who sends this header value. There is no test that confirms a correct token grants access, confirms any other value is denied, or catches the trivially-guessable value at review time.

```python
def isAdmin(request_headers):
    token = request_headers.get("X-Admin-Token", "")
    if token == ADMIN_BYPASS_TOKEN:
        return True
    return False
```

**Fix:** `test_isAdmin_correct_token`, `test_isAdmin_wrong_token`, `test_isAdmin_missing_header`, `test_remove_note_route_forbidden` (assert 403 without header), `test_remove_note_route_admin_allowed` (assert 204 with correct header).

---

#### 9. `search_notes` switched from parameterised query to f-string — SQL injection path untested · `sample-project/db.py:13` · critical · _tests_

The previous implementation used `?` placeholders (parameterised). This PR replaces it with an f-string that interpolates `user_id` and `query` directly into SQL. Because `current_user_id()` returns `int(parts[1])` from an unverified token, an attacker controls `user_id`. A crafted `query` value also injects into the LIKE clause. Neither injection vector has a test.

```python
sql = f"SELECT id, title, body FROM notes WHERE user_id = {user_id} AND title LIKE '%{query}%'"
cur.execute(sql)
```

**Fix:** `test_search_notes_sql_injection_query` — call `search_notes("' OR '1'='1", 1)` against a test DB and assert only expected rows are returned. `test_search_notes_sql_injection_user_id` — call `search_notes("", "1 OR 1=1")` and assert an error or empty result.

---

#### 10. `eval` on user-supplied expression reachable over HTTP with no test · `sample-project/app.py:46` · critical · _tests_

The route is entirely new and untested. It chains two already-untested vulnerabilities: `current_user_id()` allows identity spoofing, so the filter runs on any user's notes; the expression is passed directly to `eval()`. The error handler exposes a full Python traceback. None of these paths have a test.

```python
@app.route("/notes/filter", methods=["POST"])
def filter_notes():
    body = request.get_json()
    uid = current_user_id(request.headers.get("Authorization"))
    notes = search_notes("", uid)
    try:
        return jsonify(applyFilterExpression(notes, body["expression"]))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500
```

**Fix:** `test_filter_notes_valid_expression`, `test_filter_notes_eval_injection` (assert 400 not 200/500), `test_filter_notes_error_no_trace_leak` (assert 500 response has no `"trace"` key).

---

#### 11. `eval`-based function has no docstring — critical undisclosed risk · `sample-project/utils.py:22` · critical · _docs_

`applyFilterExpression` passes the caller-supplied `expression` string directly to `eval()` inside a list comprehension with no sandboxing, no allowlist, and no validation. This is a remote code execution vector. The function has no docstring at all, so the eval usage and its security implications are completely invisible to every downstream caller and reviewer.

```python
def applyFilterExpression(notes, expression):
    return [n for n in notes if eval(expression)]
```

**Fix:** Add a docstring with a prominent `WARNING:` block stating that `eval()` is called on unsanitised caller-supplied input and that the function must not be exposed to untrusted input until replaced with a safe evaluator.

---

#### 12. Hardcoded admin bypass token `"letmein-admin"` grants unrestricted note deletion · `sample-project/config.py:8` · high · _security_

`ADMIN_BYPASS_TOKEN = "letmein-admin"` is committed in plaintext. Anyone who reads the source code can send `X-Admin-Token: letmein-admin` and delete any note in the system. The secret is trivially guessable even without code access and cannot be rotated without a code deploy and redeploy.

```python
ADMIN_BYPASS_TOKEN = "letmein-admin"
```

**Fix:** `ADMIN_BYPASS_TOKEN = os.environ['ADMIN_BYPASS_TOKEN']` — no default; fail fast at startup. Rotate the value immediately if this commit is or was public.
**Rule:** CWE-798

---

#### 13. Tokens never expire — issued timestamp is never validated · `sample-project/auth.py:17` · high · _security_

`issue_token` embeds a Unix timestamp and its docstring claims "24 hours" validity. `current_user_id` never parses or checks the timestamp, so every token is permanently valid. A stolen or leaked token cannot be invalidated by time. Combined with the missing signature verification (finding 3), credential revocation is impossible without a database-level token blocklist.

```python
    raw = str(user_id) + "|" + str(int(time.time())) + "|" + JWT_SECRET
    return hashlib.sha1(raw.encode()).hexdigest() + "." + str(user_id)
```

**Fix:** After fixing finding 3, include the timestamp in the verifiable payload, parse it in `current_user_id`, and reject tokens where `time.time() - issued_at > 86400`.
**Rule:** CWE-613

---

#### 14. `issue_token` has no tests — output format and round-trip correctness unverified · `sample-project/auth.py:14` · high · _tests_

`issue_token()` is the only token-minting function and is depended upon by `current_user_id()` for the expected token format. No test verifies the output structure (`hex.user_id`), that the user_id round-trips correctly, or that tokens for different users are distinct.

```python
def issue_token(user_id):
    """Returns a signed JWT valid for 24 hours."""
    raw = str(user_id) + "|" + str(int(time.time())) + "|" + JWT_SECRET
    return hashlib.sha1(raw.encode()).hexdigest() + "." + str(user_id)
```

**Fix:** `test_issue_token_format` — assert result matches `r'^[0-9a-f]{40}\.7$'` for `user_id=7`. `test_issue_token_different_users_differ`. `test_issue_token_round_trip` — assert `current_user_id(issue_token(5)) == 5`.

---

#### 15. `delete_note` is new with no tests — SQL injection and silent-failure paths uncovered · `sample-project/db.py:44` · high · _tests_

`delete_note()` is entirely new. It uses an f-string for the `note_id` in a DELETE statement, making it injectable. It also swallows all exceptions silently, so callers can never observe a failure. Neither the happy path, the no-op path, nor the error path is exercised.

```python
def delete_note(note_id):
    ...
    try:
        cur.execute(f"DELETE FROM notes WHERE id = {note_id}")
        conn.commit()
    except:
        pass
```

**Fix:** `test_delete_note_deletes_row`, `test_delete_note_nonexistent_id`, `test_delete_note_sql_injection` — assert parameterisation error is raised (will pass once fixed).

---

#### 16. `DELETE /notes/<id>` route has no tests — 403 and 204 paths unchecked · `sample-project/app.py:38` · high · _tests_

The route is entirely new. No test verifies that a request without `X-Admin-Token` is rejected with 403, that a request with the correct token returns 204, or that `delete_note` is actually called.

```python
@app.route("/notes/<int:note_id>", methods=["DELETE"])
def remove_note(note_id):
    if not isAdmin(request.headers):
        return jsonify({"error": "forbidden"}), 403
    delete_note(note_id)
    return "", 204
```

**Fix:** `test_remove_note_no_token_returns_403`, `test_remove_note_valid_token_returns_204`, `test_remove_note_actually_deletes`.

---

#### 17. Docstring falsely claims the token is a JWT · `sample-project/auth.py:15` · high · _docs_

The docstring reads "Returns a signed JWT valid for 24 hours." The return value is `sha1hex + "." + user_id` — a plain SHA-1 hex digest concatenated with the user ID, not a JWT (which has three base64url-encoded segments). Callers relying on JWT-parsing libraries will fail; security reviewers auditing "JWT usage" will be misled about the token format.

**Fix:** Replace the docstring to accurately describe the `<sha1hex>.<user_id>` format, note the token is not a JWT, and document that the digest and timestamp are not verified on the read path.

---

#### 18. Docstring falsely claims tokens expire after 24 hours · `sample-project/auth.py:15` · high · _docs_

The docstring states "valid for 24 hours" but `current_user_id()` does not parse the token, verify the digest, or inspect the embedded timestamp. A token issued by `issue_token` is valid forever. This is a separate inaccuracy from finding 17 in the same docstring.

**Fix:** Add to the docstring: "There is no expiry enforcement — `current_user_id()` does not validate the digest or the timestamp embedded in the token."

---

#### 19. Security-critical authentication function has no docstring · `sample-project/auth.py:20` · high · _docs_

`current_user_id` is the sole authentication gate for `search`, `create_note`, and `filter_notes`. It has no docstring. The function accepts any string matching `<anything>.<integer>` as a valid identity — the SHA-1 prefix is never verified. This behaviour and its security implication are entirely invisible to callers.

**Fix:** Add a docstring documenting the accepted token format, the `None` return contract, and a clear warning that the SHA-1 prefix is not verified and tokens do not expire.

---

#### 20. Security-critical authorisation function has no docstring · `sample-project/auth.py:29` · high · _docs_

`isAdmin` controls access to the admin deletion endpoint. It has no docstring. The bare string comparison against a hardcoded config value (`"letmein-admin"`) is invisible to callers, as is the fact that admin access is controlled solely by a single static secret with no per-user identity.

**Fix:** Add a docstring documenting the `X-Admin-Token` header, the config source, the plain string equality comparison (not constant-time), and the `bool` return type.

---

#### 21. `applyFilterExpression` uses camelCase — violates naming rules 1.1 and 1.4 · `sample-project/utils.py:22` · high · _style_

Rule 1.1 requires `snake_case` for all functions. `applyFilterExpression` uses camelCase.

```python
def applyFilterExpression(notes, expression):
```

**Fix:** Rename to `apply_filter_expression` and update the import and call site in `app.py`.
**Rule:** 1.1

---

#### 22. Import of `applyFilterExpression` propagates naming violation · `sample-project/app.py:7` · high · _style_

Downstream of finding 21. Fixed automatically when finding 21 is resolved.

```python
from utils import slugify, truncate, parse_tags, applyFilterExpression
```

**Fix:** Update to `apply_filter_expression` once `utils.py` is corrected.
**Rule:** 1.1

---

#### 23. `isAdmin` uses camelCase and fails predicate naming contract · `sample-project/auth.py:29` · high · _style_

Rule 1.1 requires `snake_case` for all functions; rule 1.4 requires boolean-returning functions to use the `is_`/`has_` predicate form. `isAdmin` violates both rules. _[Merged: STY-3 + STY-4]_

```python
def isAdmin(request_headers):
```

**Fix:** Rename to `is_admin` and update all import and call sites.
**Rule:** 1.1, 1.4

---

#### 24. Import of `isAdmin` propagates naming violation · `sample-project/app.py:6` · high · _style_

Downstream of finding 23. Fixed automatically when finding 23 is resolved.

```python
from auth import current_user_id, isAdmin, hash_password, verify_password
```

**Fix:** Update to `is_admin` once `auth.py` is corrected.
**Rule:** 1.1

---

#### 25. `import traceback` placed after third-party import — wrong import order · `sample-project/app.py:2` · high · _style_

Rule 2.2 requires stdlib → (blank line) → third-party → (blank line) → first-party. `from flask import ...` (third-party) precedes `import traceback` (stdlib) with no blank-line separation.

```python
from flask import Flask, request, jsonify
import traceback
```

**Fix:** Reorder: `import traceback` first, blank line, then `from flask import ...`, blank line, then first-party imports.
**Rule:** 2.2

---

#### 26. Wildcard import from config (pre-existing) · `sample-project/db.py:2` · high · _style_

Rule 2.1 forbids `from x import *`. Every name in `config.py` is silently pulled into `db.py`'s namespace, defeating static analysis and making symbol origins unknowable. In_diff: false.

```python
from config import *
```

**Fix:** Replace with explicit imports of only the names `db.py` actually uses, e.g. `from config import DATABASE_URL`.
**Rule:** 2.1

---

#### 27. `insertNote` uses camelCase name (pre-existing) · `sample-project/db.py:29` · high · _style_

Rule 1.1 requires `snake_case`. `insertNote` is camelCase. Pre-existing; in_diff: false.

```python
def insertNote(title, body, user_id, tags=[]):
```

**Fix:** Rename to `insert_note` and update all call sites.
**Rule:** 1.1

---

#### 28. Mutable default argument `tags=[]` in `insertNote` (pre-existing) · `sample-project/db.py:29` · high · _style_

Rule 3.1 forbids mutable default arguments. The list `[]` is created once at definition time and shared across every call that omits `tags`. Pre-existing; in_diff: false.

**Fix:** Change to `tags=None` and add `if tags is None: tags = []` at the top of the body.
**Rule:** 3.1

---

### Should fix

#### 29. `except:` block contains only `pass` in `delete_note` — errors silently swallowed · `sample-project/db.py:50` · medium (bare `except`) and `sample-project/db.py:51` · medium (only `pass`) · _style_

Rule 4.1 forbids bare `except:` (catches `SystemExit`, `KeyboardInterrupt`, `GeneratorExit`). Rule 4.2 forbids an `except` block containing only `pass`. If the error is genuinely ignorable, the rule requires logging it and a comment explaining why.

```python
    except:
        pass
```

**Fix:** `except sqlite3.DatabaseError as e: logging.warning("delete_note failed: %s", e)  # row may not exist; caller does not need to know`
**Rule:** 4.1, 4.2

---

#### 30. Passwords hashed with unsalted MD5 — trivially crackable (pre-existing) · `sample-project/auth.py:7` · medium · _security_

`hash_password` uses `hashlib.md5` with no salt. MD5 is cryptographically broken; precomputed rainbow tables exist for common passwords. This was pre-existing but is now actively exercised via `/auth/register`, elevating it from latent to actively exploitable. In_diff: false.

```python
    return hashlib.md5(password.encode()).hexdigest()
```

**Fix:** Replace with `bcrypt`, `scrypt`, or Argon2. Update `verify_password` accordingly and plan a migration of existing hashes.
**Rule:** CWE-916

---

#### 31. Pre-existing hardcoded `JWT_SECRET` now actively used for token signing · `sample-project/config.py:6` · medium · _security_

`JWT_SECRET` was already hardcoded before this PR. This PR activates it: `issue_token` now uses it as the sole signing material. Even if finding 3 is fixed and signatures are verified, the secret is committed to version control and known to anyone with repo access. In_diff: false.

```python
JWT_SECRET = "FAKE_NOT_A_REAL_KEY_s3cr3t_signing_key_2026"
```

**Fix:** `JWT_SECRET = os.environ['JWT_SECRET']` — no default; fail fast. Rotate and invalidate all outstanding tokens after deployment.
**Rule:** CWE-798

---

#### 32. `delete_note` has no docstring; silent exception swallowing undocumented · `sample-project/db.py:44` · medium · _docs_

`delete_note` has no docstring. Its `except: pass` block silently discards all exceptions — callers (including `remove_note`) have no way to determine whether the delete succeeded or failed. This behaviour is completely undocumented.

**Fix:** Add a docstring explicitly noting that all database exceptions are silently swallowed and that the function returns `None` regardless of success or failure.

---

#### 33. DELETE route has no docstring; auth requirement and silent-failure invisible · `sample-project/app.py:39` · medium · _docs_

`remove_note` has no docstring. Two important behaviours are invisible: the route requires a valid `X-Admin-Token` header; and it calls `delete_note` which silently swallows exceptions, so a 204 response does not guarantee the note was actually deleted.

**Fix:** Add a docstring documenting the `X-Admin-Token` requirement, the 403 response for missing/wrong token, and the silent-failure caveat.

---

#### 34. POST filter route has no docstring; eval risk and traceback leak invisible · `sample-project/app.py:47` · medium · _docs_

`filter_notes` has no docstring. Two significant behaviours are invisible: it delegates to `applyFilterExpression` which calls `eval()` on the caller-supplied `expression` field; and on any exception it returns the full server-side traceback in the JSON response body.

**Fix:** Add a docstring documenting the `expression` field semantics, the `eval()` usage with a security warning, and the traceback-leak in error responses.

---

#### 35. `truncate` ellipsis branch has no test (pre-existing gap) · `sample-project/utils.py:11` · medium · _tests_

The only existing test for `truncate` exercises the short-text branch. The ellipsis branch is unreachable by any test. Surfaced here because `truncate` is called in the `/notes/search` response and its output contract is material to the API. In_diff: false.

```python
def truncate(text, length=140):
    if len(text) <= length:
        return text
    return text[:length] + "..."
```

**Fix:** `test_truncate_long_text_ellipsis` — call `truncate('a' * 200)` and assert the result is `'a' * 140 + '...'` and `len(result) == 143`.

---

### Test coverage

The existing test suite covers only `slugify` (2 cases) and the short-text branch of `truncate` (1 case). Every new or changed symbol in this PR is entirely untested.

| Added or changed | Tested | Suggested test |
|---|---|---|
| `applyFilterExpression` | ❌ | `test_applyFilterExpression_simple_predicate`, `test_applyFilterExpression_code_injection` |
| `current_user_id` | ❌ | `test_current_user_id_valid_token`, `test_current_user_id_forged_token`, `test_current_user_id_missing_token` |
| `isAdmin` | ❌ | `test_isAdmin_correct_token`, `test_isAdmin_wrong_token`, `test_isAdmin_missing_header` |
| `issue_token` | ❌ | `test_issue_token_format`, `test_issue_token_round_trip`, `test_issue_token_different_users_differ` |
| `search_notes` (changed) | ❌ | `test_search_notes_sql_injection_query`, `test_search_notes_sql_injection_user_id` |
| `delete_note` | ❌ | `test_delete_note_deletes_row`, `test_delete_note_nonexistent_id`, `test_delete_note_sql_injection` |
| `remove_note` DELETE route | ❌ | `test_remove_note_no_token_returns_403`, `test_remove_note_valid_token_returns_204` |
| `filter_notes` POST route | ❌ | `test_filter_notes_eval_injection`, `test_filter_notes_error_no_trace_leak`, `test_filter_notes_valid_expression` |
| `truncate` ellipsis branch | ❌ | `test_truncate_long_text_ellipsis` |

---

### Reviewer status

| Reviewer | Status | Findings | Time |
|---|---|---|---|
| security-reviewer | ✅ ok | 9 | ~16s |
| style-reviewer | ✅ ok | 12 | ~16s |
| test-coverage-reviewer | ✅ ok | 9 | ~15s |
| docs-reviewer | ✅ ok | 8 | ~15s |

2 findings were reported by more than one reviewer and merged:
- **Finding 5** (traceback in HTTP response body): SEC-6 [security, high] + STY-8 [style, critical] → merged as [security, style], critical — highest severity kept
- **Finding 23** (`isAdmin` naming): STY-3 [style, rule 1.1] + STY-4 [style, rule 1.4] → merged as [style], high — both rules cited, single fix

---

### Checked and clean

- `sample-project/db.py`: `get_note` and `insertNote` body — use parameterised queries correctly and are not modified by this diff
- `sample-project/utils.py`: `slugify`, `truncate`, `parse_tags` — unmodified and safe
- `sample-project/app.py`: `/auth/register` endpoint — input handled safely
- `sample-project/app.py`: Flask route type converter `<int:note_id>` — constrains `note_id` to integer at the HTTP routing layer (provides defence-in-depth for finding 4, but does not substitute for parameterised queries in the DB function)
- `sample-project/config.py`: structure is otherwise correct; new constant follows `SCREAMING_SNAKE_CASE` convention (rule 1.3) — the problem is the value, not the naming

### Not checked

- Database schema and migrations — not present in the diff or repository
- Dependency versions and third-party library CVEs — `requirements.txt` not changed in this diff; no lockfile present
- Flask session/cookie configuration — not modified by this diff
- TLS/transport security configuration — infrastructure-level, out of diff scope
- Rate-limiting and brute-force protection — not present in any reviewed file
- Integration and end-to-end tests — PR author deferred these; out of scope for static analysis

---

<sub>Generated by four IBM Bob subagents running in parallel, synthesized in Agent
mode. Wall clock ~62s. Provenance for every finding is in
`reviews/raw/`.</sub>
