## Review: Add saved filters and admin note deletion

**Request changes** — 4 critical, 6 high, 7 medium, 2 low
across 5 files. Reviewed by four parallel passes in ~60s.

This PR introduces two high-value features but ships four exploitable vulnerabilities in the diff itself: a server-side remote code execution via `eval`, two SQL injections (one introduced by deliberately removing a parameterised query), a broken authentication scheme that accepts any forged token as valid identity, and a hardcoded admin bypass token. The auth plumbing, the filter endpoint, and the delete endpoint each carry at least one critical or high defect. The test suite is unchanged despite every security-sensitive path being new code. Do not merge without addressing at minimum the critical findings.

---

### Must fix before merge

#### 1. `eval()` on user-supplied filter expression allows full RCE · `sample-project/utils.py:22` · critical · _security_

The `expression` value comes directly from the POST body sent by any authenticated caller and is passed without sanitisation to Python's built-in `eval()`. An attacker can execute arbitrary OS commands (e.g. `__import__('os').system('...')`) or read the filesystem with no additional privileges. Because authentication itself is broken (see finding 3), this endpoint is reachable without valid credentials.

```python
return [n for n in notes if eval(expression)]
```

**Fix:** Remove `eval` entirely. Implement a restricted filter by parsing an allowlisted set of field/operator/value triples, e.g.:

```python
ALLOWED_FIELDS = {"title", "body"}
def apply_filter_expression(notes, field, op, value):
    if field not in ALLOWED_FIELDS or op not in ("contains", "eq"):
        raise ValueError("invalid filter")
    return [n for n in notes if value in n[FIELD_MAP[field]]]
```
**Rule:** CWE-95

---

#### 2. SQL injection via f-string interpolation in `search_notes` · `sample-project/db.py:13` · critical · _security_

The previous parameterised query was replaced with direct f-string interpolation of both `user_id` (attacker-controlled via forged token — see finding 3) and `query` (a raw URL parameter). Either value can break out of the SQL context to read, modify, or drop arbitrary tables. The PR description frames this as a user-requested wildcard feature; that framing does not justify removing parameterised queries.

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
**Rule:** CWE-89

---

#### 3. Token contains user_id in plaintext with no signature verification · `sample-project/auth.py:26` · critical · _security_

`current_user_id` splits the token on `.` and returns `int(parts[1])` directly — it never checks the SHA-1 signature stored in `parts[0]`. Any caller can craft `<anything>.<target_user_id>` and impersonate any user in the system. This also means the SQL injection surface in `search_notes` and `insertNote` is fully attacker-controlled.

```python
parts = token.split(".")
if len(parts) != 2:
    return None
return int(parts[1])
```

**Fix:** Verify the HMAC before trusting the payload:

```python
def current_user_id(token):
    if not token:
        return None
    parts = token.split(".")
    if len(parts) != 2:
        return None
    sig, user_id = parts[0], parts[1]
    expected = hashlib.sha1((user_id + "|" + JWT_SECRET).encode()).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    return int(user_id)
```
Longer-term, replace the hand-rolled scheme with a standard JWT library (e.g. PyJWT).
**Rule:** CWE-345

---

#### 4. SQL injection in `delete_note` via f-string interpolation · `sample-project/db.py:48` · critical · _security_

Although Flask's `<int:note_id>` route converter guarantees an integer at the routing layer, the function signature accepts any value and interpolates it directly into SQL. If `delete_note` is ever called from a non-route context with an unsanitised value the injection is exploitable. Defensively, all DB functions must use parameterised queries regardless of call site.

```python
cur.execute(f"DELETE FROM notes WHERE id = {note_id}")
```

**Fix:** `cur.execute("DELETE FROM notes WHERE id = ?", (note_id,))`
**Rule:** CWE-89

---

#### 5. Stack trace returned to caller on unhandled exception · `sample-project/app.py:54` · critical · _security, style_

The exception handler in `filter_notes` serialises both `str(e)` and `traceback.format_exc()` into the JSON response body. Stack traces disclose internal file paths, library versions, variable names, and interpreter internals — confirming to an attacker that `eval` is in play and showing which expression fragment caused an error. This is also an explicit violation of style rule 4.3. _[Merged finding: SEC-6 + STY-3]_

```python
return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500
```

**Fix:** Log server-side, return a generic message to the caller:

```python
import logging
logger = logging.getLogger(__name__)
# ...
except Exception as e:
    logger.exception("filter_notes failed")
    return jsonify({"error": "internal server error"}), 500
```
**Rule:** CWE-209 / style 4.3

---

#### 6. Hardcoded admin bypass token `"letmein-admin"` committed to source · `sample-project/auth.py:31` · high · _security_

The admin check compares the `X-Admin-Token` header against the hardcoded string `"letmein-admin"` imported from `config.py`. The secret is trivially guessable, committed to source control, and cannot be rotated without a code deploy. Any attacker who reads the repository gains permanent admin access to delete any note.

```python
ADMIN_BYPASS_TOKEN = "letmein-admin"
# ...
if token == ADMIN_BYPASS_TOKEN:
    return True
```

**Fix:** Source from an environment variable with no default — fail fast at startup:

```python
ADMIN_BYPASS_TOKEN = os.environ["ADMIN_BYPASS_TOKEN"]
```
Longer-term, replace the shared secret with per-user role checks stored in the database.
**Rule:** CWE-798

---

#### 7. JWT_SECRET hardcoded in source; used as HMAC key for all tokens · `sample-project/config.py:6` · high · _security_

`JWT_SECRET` is committed directly to source control. Because `issue_token` uses it as the sole signing key, anyone who can read the repository can forge arbitrary tokens for any user. This pre-existing defect is now actively exploitable since `current_user_id` is wired into auth-sensitive endpoints (search, create, filter). In_diff: false.

```python
JWT_SECRET = "FAKE_NOT_A_REAL_KEY_s3cr3t_signing_key_2026"
```

**Fix:** `JWT_SECRET = os.environ["JWT_SECRET"]  # no default; fail fast`
**Rule:** CWE-321

---

#### 8. `applyFilterExpression` uses `eval()` with no tests · `sample-project/utils.py:22` · critical · _tests_

No tests verify that the `eval`-based path refuses malicious expressions, returns the correct type for valid predicates, or behaves predictably on exceptions. Any attacker reaching `POST /notes/filter` can run arbitrary Python in the server process with no automated guard to detect a regression.

```python
def applyFilterExpression(notes, expression):
    return [n for n in notes if eval(expression)]
```

**Fix:** Add `test_apply_filter_expression_arbitrary_code_execution` — assert an expression like `'__import__("os").getenv("HOME")'` raises or is refused; add `test_apply_filter_expression_valid` with a known note list and safe predicate.

---

#### 9. `search_notes` changed to f-string — SQL injection path untested · `sample-project/db.py:13` · critical · _tests_

The PR removed parameterised placeholders without adding any test to guard the new form. There is no automated check that `q="' OR '1'='1"` doesn't leak all rows, or that `user_id=None` raises rather than interpolating `None` literally into SQL.

```python
sql = f"SELECT id, title, body FROM notes WHERE user_id = {user_id} AND title LIKE '%{query}%'"
```

**Fix:** Add `test_search_notes_sql_injection` — call against a test DB with an injection payload and assert only rows for the target user are returned.

---

#### 10. `POST /notes/filter` route has no tests — eval-based RCE reachable with no guard · `sample-project/app.py:46` · critical · _tests_

No test checks that malicious expressions are blocked, that the 500 path does not leak a traceback to the caller, or that only the authenticated user's notes are visible. The most dangerous new endpoint in this PR has zero test coverage.

```python
@app.route("/notes/filter", methods=["POST"])
def filter_notes():
    ...
    return jsonify(applyFilterExpression(notes, body["expression"]))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500
```

**Fix:** Add `test_filter_notes_rce_expression`, `test_filter_notes_traceback_not_leaked`, and `test_filter_notes_valid_expression`.

---

#### 11. `isAdmin` has no tests — hardcoded bypass token goes unvalidated · `sample-project/auth.py:29` · critical · _tests_

The admin gate is a single string equality check against `"letmein-admin"`. No test verifies that a missing, empty, or wrong token is rejected, or documents the expected token-rotation mechanism (currently none).

```python
def isAdmin(request_headers):
    token = request_headers.get("X-Admin-Token", "")
    if token == ADMIN_BYPASS_TOKEN:
        return True
    return False
```

**Fix:** `test_is_admin_correct_token`, `test_is_admin_wrong_token`, `test_is_admin_missing_header`.

---

### Should fix

#### 12. Docstring falsely claims return value is a JWT · `sample-project/auth.py:15` · high · _docs_

Callers and reviewers reading the docstring will assume the token is a standards-compliant JWT (three base64url segments, verifiable with any JWT library). In reality the function returns a two-part string `sha1hex.user_id`. Code that tries to decode or verify it as a JWT will fail silently or with a misleading error.

**Fix:** Replace the docstring: _"Returns a token of the form `<sha1hex>.<user_id>`. The sha1 is computed over `user_id + '|' + unix_timestamp + '|' + JWT_SECRET`. Note: expiry is embedded but NOT verified by `current_user_id()`."_

---

#### 13. Docstring claims tokens expire after 24 hours — expiry is never enforced · `sample-project/auth.py:15` · high · _docs_

A caller reading "valid for 24 hours" will assume old tokens are automatically rejected. `current_user_id()` never inspects the timestamp — tokens are valid indefinitely. (Note: this is a separate inaccuracy in the same docstring as finding 12; both must be corrected.)

**Fix:** Add to the docstring: _"The timestamp is embedded in the token but expiry is not enforced by `current_user_id()`; tokens do not expire."_

---

#### 14. `current_user_id` has no tests — token parsing is trivially bypassable · `sample-project/auth.py:20` · high · _tests_

No assertion exists that a crafted token like `"anything.999"` is rejected, that `None` is returned for missing/malformed tokens, or that an attacker cannot impersonate any user.

**Fix:** `test_current_user_id_forged_token` — assert `current_user_id("forged.42")` does NOT return 42; `test_current_user_id_missing_token`; `test_current_user_id_malformed_token`.

---

#### 15. `issue_token` has no tests — token format and signature unverified · `sample-project/auth.py:14` · high · _tests_

No assertion verifies the produced token has the expected format, that `current_user_id` can round-trip it, or that changing `JWT_SECRET` produces a different hash.

**Fix:** `test_issue_token_format`, `test_issue_token_roundtrip`, `test_issue_token_secret_sensitivity`.

---

#### 16. `delete_note` has no tests — silent exception suppression and SQL injection unverified · `sample-project/db.py:44` · high · _tests_

Bare `except/pass` silently swallows all DB errors; the f-string SQL injection is also unguarded. Neither the happy-path deletion nor the silent-failure branch is verified.

**Fix:** `test_delete_note_removes_row`, `test_delete_note_sql_injection`, `test_delete_note_nonexistent_id`.

---

#### 17. `DELETE /notes/<id>` route has no tests — admin gate and deletion response unverified · `sample-project/app.py:38` · high · _tests_

No assertion verifies that a request without `X-Admin-Token` returns 403, that a correct-token request returns 204, or that the route actually invokes `delete_note`.

**Fix:** `test_remove_note_forbidden`, `test_remove_note_success`.

---

#### 18. Bare `except:` catches all exceptions including `BaseException` · `sample-project/db.py:50` · high · _style_

Rule 4.1 forbids bare `except:` — it catches `KeyboardInterrupt` and `SystemExit`, masking serious failures and making debugging impossible.

```python
    except:
        pass
```

**Fix:** Catch the narrowest applicable exception: `except Exception as e:`
**Rule:** 4.1

---

#### 19. `except` block contains only `pass` — errors silently swallowed · `sample-project/db.py:51` · high · _style_

Rule 4.2 forbids an `except` block containing only `pass`. A DELETE failure (constraint violation, connection error) is completely invisible. If genuinely ignorable, log it and add a comment saying why.

**Fix:** `except Exception as e: logger.warning("delete_note failed for id=%s: %s", note_id, e)`
**Rule:** 4.2

---

#### 20. Wildcard import from config · `sample-project/db.py:2` · high · _style_

Rule 2.1 forbids `from x import *`. It defeats static analysis and makes the origin of every name in `db.py` unknowable. Pre-existing, but present in diff context. In_diff: false.

**Fix:** `from config import DATABASE_URL` (and any other symbols actually used in this module).
**Rule:** 2.1

---

#### 21. No docstring on `applyFilterExpression` — dangerous `eval` is completely undocumented · `sample-project/utils.py:22` · high · _docs_

The absence of any docstring means neither the route author nor future maintainers will notice the code-execution risk from reading the signature alone. _Note: docs-reviewer rated this critical; security-reviewer's separate RCE finding (finding 1) captures the exploitability. Docstring gap rated high here as a standalone issue._

**Fix:** Add a docstring with a prominent security warning that `eval` is used and untrusted input must not be passed until a safe evaluator replaces it.

---

#### 22. No docstring on `current_user_id` — signature bypass invisible to callers · `sample-project/auth.py:20` · medium · _docs_

Without a docstring, callers do not know the function returns `None` (not raises) on a missing/malformed token, or that the user_id is taken from the token's second segment with no signature verification.

**Fix:** Document accepted token format, return type, and the critical warning that the signature is not verified.

---

#### 23. No docstring on `isAdmin` — header name and secret source invisible · `sample-project/auth.py:29` · medium · _docs_

Reviewers do not know which header is inspected (`X-Admin-Token`), that the comparison is against a hardcoded config value, or that there is no rate-limiting or HMAC protection.

**Fix:** Document the header name, config source, and bare string-equality behaviour.

---

#### 24. `isAdmin` function name violates snake_case (rules 1.1 and 1.4) · `sample-project/auth.py:29` · medium · _style_

`isAdmin` uses camelCase (violates rule 1.1) and fails the predicate naming contract `is_admin` (violates rule 1.4). _[Merged STY-4 + STY-5]_

```python
def isAdmin(request_headers):
```

**Fix:** Rename to `is_admin` and update all call sites.
**Rule:** 1.1, 1.4

---

#### 25. `applyFilterExpression` function name violates snake_case · `sample-project/utils.py:22` · medium · _style_

Rule 1.1 requires all functions to use snake_case.

```python
def applyFilterExpression(notes, expression):
```

**Fix:** Rename to `apply_filter_expression` and update the import in `app.py`.
**Rule:** 1.1

---

#### 26. `applyFilterExpression` import name is camelCase · `sample-project/app.py:7` · medium · _style_

Flows directly from the definition violation above. In_diff: true.

**Fix:** Follows automatically from renaming the definition (finding 25).
**Rule:** 1.1

---

#### 27. `isAdmin` import name is camelCase · `sample-project/app.py:6` · medium · _style_

Flows directly from finding 24.

**Fix:** Follows automatically from renaming the definition (finding 24).
**Rule:** 1.1

---

#### 28. `insertNote` uses camelCase name and mutable default `tags=[]` · `sample-project/db.py:29` · medium · _style_

Pre-existing. Rule 1.1 (camelCase) and rule 3.1 (mutable default argument — the default list is created once at definition time and shared across all calls). In_diff: false.

```python
def insertNote(title, body, user_id, tags=[]):
```

**Fix:** Rename to `insert_note`; change signature to `tags=None` with `if tags is None: tags = []` in the body.
**Rule:** 1.1, 3.1

---

#### 29. No docstring on `delete_note` — silent error suppression invisible · `sample-project/db.py:44` · medium · _docs_

The `except: pass` behaviour (a failed DELETE returns `None` with no indication of failure) is completely hidden from callers. The calling route always responds 204, giving the admin no way to tell whether deletion succeeded.

**Fix:** Add a docstring documenting the silent-failure behaviour explicitly.

---

#### 30. Token includes a timestamp but expiry is never validated · `sample-project/auth.py:17` · medium · _security_

The docstring claims "valid for 24 hours" and a timestamp is embedded, but `current_user_id` never reads or checks the timestamp. Tokens are valid forever, meaning a stolen token cannot be invalidated by time alone.

**Fix:** Include the expiry in the verifiable payload and check it in `current_user_id`. Prefer PyJWT.
**Rule:** CWE-613

---

#### 31. Passwords hashed with MD5 — no salt, cryptographically broken · `sample-project/auth.py:7` · medium · _security_

MD5 is fast and unsalted — rainbow tables exist for common passwords. Pre-existing but now elevated because `verify_password` is wired into live authentication flows by this PR. In_diff: false.

**Fix:** Replace with argon2, bcrypt, or scrypt.
**Rule:** CWE-916

---

### Consider

- **No docstring on DELETE route `remove_note`** · `sample-project/app.py:39` · _docs_ — Auth requirement and silent-failure behaviour undocumented; developers wiring clients have no inline guidance.
- **No docstring on filter route `filter_notes`** · `sample-project/app.py:47` · _docs_ — `eval` risk and full traceback leak are invisible from the route signature alone.

---

### Test coverage

The existing test suite covers only `slugify` (2 cases) and the short-text branch of `truncate` (1 case). Every new and changed symbol in this PR is untested.

| Added or changed | Tested | Suggested test |
|---|---|---|
| `applyFilterExpression` | ❌ | `test_apply_filter_expression_rce_blocked`, `test_apply_filter_expression_valid` |
| `current_user_id` | ❌ | `test_current_user_id_forged_token`, `test_current_user_id_none`, `test_current_user_id_malformed` |
| `isAdmin` | ❌ | `test_is_admin_correct_token`, `test_is_admin_wrong_token`, `test_is_admin_missing` |
| `issue_token` | ❌ | `test_issue_token_format`, `test_issue_token_roundtrip`, `test_issue_token_secret_sensitivity` |
| `search_notes` (changed) | ❌ | `test_search_notes_sql_injection`, `test_search_notes_none_user_id` |
| `delete_note` | ❌ | `test_delete_note_removes_row`, `test_delete_note_sql_injection`, `test_delete_note_nonexistent` |
| `remove_note` (DELETE route) | ❌ | `test_remove_note_forbidden`, `test_remove_note_success` |
| `filter_notes` (POST route) | ❌ | `test_filter_notes_rce_expression`, `test_filter_notes_traceback_not_leaked`, `test_filter_notes_valid` |
| `truncate` (ellipsis branch) | ❌ | `test_truncate_long_text_appends_ellipsis`, `test_truncate_exact_boundary` |

---

### Reviewer status

| Reviewer | Status | Findings | Time |
|---|---|---|---|
| security-reviewer | ✅ ok | 9 | ~15s |
| style-reviewer | ✅ ok (schema repaired: `violations` → `findings`) | 11 | ~15s |
| test-coverage-reviewer | ✅ ok (schema repaired: bare array → wrapped object) | 9 | ~15s |
| docs-reviewer | ✅ ok (schema repaired: bare array → wrapped object) | 8 | ~15s |

2 findings were reported by more than one reviewer and merged:
- **Finding 5** (traceback in HTTP response): SEC-6 [security, high] + STY-3 [style, critical] → merged as [security, style], critical
- **Finding 24** (isAdmin naming): STY-4 [rule 1.1] + STY-5 [rule 1.4] → merged as single finding citing both rules

---

### Checked and clean

- `sample-project/db.py`: `get_note`, `insertNote` body — use parameterised queries correctly
- `sample-project/utils.py`: `slugify`, `truncate`, `parse_tags` — no injection surface, no security defects
- `sample-project/app.py`: `/auth/register` endpoint — input handled safely
- `sample-project/app.py`: Flask route type converter `<int:note_id>` constrains `note_id` to integer at the routing layer
- `sample-project/app.py`: import order within the diff block is consistent with existing module structure

### Not checked

- Database schema and migrations — not present in diff or repository
- Dependency versions / third-party library CVEs — `requirements.txt` not changed in this diff; no lockfile present
- Integration and end-to-end tests — PR author deferred these; they are out of scope for static analysis
- Rate-limiting, brute-force protection, and CORS configuration — not present in any reviewed file
- Production deployment configuration (environment variable injection, secrets management) — out of scope for code review

---

<sub>Generated by four IBM Bob subagents running in parallel, synthesized in Agent mode. Wall clock ~60s. Provenance for every finding is in `reviews/raw/`.</sub>
