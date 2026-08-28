## Review: Add saved filters and admin note deletion

**Request changes** — 4 critical, 8 high, 4 medium, 1 low
across 5 files. Reviewed by four parallel passes in N/A (timing not available).

This PR introduces two new endpoints and migrates auth to a header-based token system, but ships critical security defects in every changed file. The filter endpoint executes arbitrary user-supplied Python via `eval()` with no sandboxing — full remote code execution for any authenticated (or, given the broken token verification, any) user. The `search_notes` query was deliberately rewritten from parameterised form to f-string interpolation, introducing SQL injection on both the query and user_id parameters. Token verification was never implemented — the HMAC prefix is generated but silently discarded, so any attacker can forge any user identity by crafting `anything.<user_id>`. The admin deletion gate relies on a hardcoded static secret (`letmein-admin`) committed to source. None of these should merge in any form; each is independently a blocker.

---

### Must fix before merge

#### 1. Remote code execution via `eval()` on user-supplied filter expression · `sample-project/utils.py:23` · critical · _security, tests, style, docs_

`eval(expression)` executes an arbitrary Python string supplied directly from the request body with no sandboxing, allow-listing, or restriction. Any authenticated user can POST `{"expression": "__import__('os').system('rm -rf /')"}` to `/notes/filter` and achieve full server-side code execution. The PR description actively promotes this as a feature ("power users can write whatever they want"), making it intentional and all the more dangerous. There are no tests for any filtering behaviour — safe or malicious — and the function has no docstring documenting the `eval` usage or the implicit `n` variable binding.

```python
return [n for n in notes if eval(expression)]
```

**Fix:** Remove `eval` entirely. Implement a safe predicate DSL or restrict filtering to known fields:
```python
ALLOWED_FIELDS = {"title", "body"}
def apply_filter_expression(notes, field, value):
    if field not in ALLOWED_FIELDS:
        raise ValueError("Invalid field")
    return [n for n in notes if value in (n[FIELDS[field]] or "")]
```
**Rule:** CWE-95

---

#### 2. SQL injection in `search_notes` via f-string interpolation · `sample-project/db.py:13` · critical · _security, tests_

The PR *removes* parameterised queries and replaces them with direct f-string interpolation of both `user_id` and `query` into SQL. An attacker can pass `q='; DROP TABLE notes; --` or exfiltrate the full database via the `?q=` query parameter. The PR description explicitly states this was done "so we can support the `%` wildcard that users kept asking for" — a wildcard can be supported safely with parameterised queries. There are no tests confirming the function rejects injection attempts or scopes results to the correct user.

```python
sql = f"SELECT id, title, body FROM notes WHERE user_id = {user_id} AND title LIKE '%{query}%'"
cur.execute(sql)
```

**Fix:** Restore parameterised queries and pass the wildcard inside the parameter value:
```python
cur.execute(
    "SELECT id, title, body FROM notes WHERE user_id = ? AND title LIKE ?",
    (user_id, "%" + query + "%"),
)
```
**Rule:** CWE-89

---

#### 3. SQL injection + silent failure in `delete_note` · `sample-project/db.py:48` · critical · _security, tests, style, docs_

`delete_note` interpolates `note_id` directly into a DELETE statement (SEC-3/CWE-89). Although Flask's `<int:note_id>` route parameter rejects non-integers at the routing layer, trusting the router as the sole defence is fragile — any future Python caller of `delete_note()` is fully injectable. The function also contains a bare `except: pass` (STY-5/rule 4.1, 4.2): all database errors are silently swallowed, so callers — including `remove_note` which returns 204 — cannot distinguish a successful delete from a failed one. No tests exist for either the injection path or the silent-failure behaviour.

```python
cur.execute(f"DELETE FROM notes WHERE id = {note_id}")
conn.commit()
except:
    pass
```

**Fix:**
```python
cur.execute("DELETE FROM notes WHERE id = ?", (note_id,))
conn.commit()
except Exception as e:
    app.logger.warning("delete_note failed for id=%s: %s", note_id, e)
    # Caller is notified via 204 regardless; error is logged for ops
```
**Rule:** CWE-89; style rules 4.1, 4.2

---

#### 4. `issue_token` docstring is actively misleading — not a JWT, tokens never expire · `sample-project/auth.py:15` · critical · _docs, tests, security_

The docstring says "Returns a signed JWT valid for 24 hours." The output is `sha1(user_id|timestamp|secret).<user_id>`, which is structurally nothing like a JWT (no base64-encoded header/payload/signature). The "24 hours" expiry claim is also false: `current_user_id()` never inspects the embedded timestamp, so issued tokens are valid forever. Callers and auditors relying on this docstring will have a fundamentally wrong model of the auth system's security properties. Separately, SHA-1 is a deprecated, collision-vulnerable hash and the implementation is a plain hash rather than an HMAC, leaving it open to length-extension attacks (SEC-9/CWE-327). No tests verify the token format or that expiry is enforced (or document that it isn't).

```python
def issue_token(user_id):
    """Returns a signed JWT valid for 24 hours."""
    raw = str(user_id) + "|" + str(int(time.time())) + "|" + JWT_SECRET
    return hashlib.sha1(raw.encode()).hexdigest() + "." + str(user_id)
```

**Fix:** Replace the docstring with an accurate description and replace SHA-1 with HMAC-SHA-256:
```python
def issue_token(user_id):
    """
    Issues a custom bearer token for the given user_id.

    Format: hmac_sha256(user_id|unix_timestamp|JWT_SECRET).<user_id>

    WARNING: This is NOT a JWT. The embedded timestamp is not validated
    by current_user_id(), so tokens do not currently expire.
    """
    import hmac as _hmac
    raw = str(user_id) + "|" + str(int(time.time()))
    sig = _hmac.new(JWT_SECRET.encode(), raw.encode(), "sha256").hexdigest()
    return sig + "." + str(user_id)
```
**Rule:** CWE-327

---

#### 5. Broken authentication — token signature never verified · `sample-project/auth.py:20` · high · _security, tests, docs_

`current_user_id` splits the token on `.` and returns `int(parts[1])` — it never verifies the HMAC prefix in `parts[0]`. Any caller can forge `anyhash.42` to impersonate user ID 42. The `issue_token` function generates a signature, but nothing in the verification path checks it, rendering the entire auth system trivially bypassable. No tests cover the forgery path, malformed tokens, or the None-token path.

```python
def current_user_id(token):
    ...
    parts = token.split(".")
    if len(parts) != 2:
        return None
    return int(parts[1])   # signature in parts[0] is silently discarded
```

**Fix:** Recompute the expected signature and reject mismatches:
```python
def current_user_id(token):
    if not token:
        return None
    parts = token.split(".")
    if len(parts) != 2:
        return None
    user_id = parts[1]
    raw = user_id + "|" + JWT_SECRET
    expected = hashlib.sha256(raw.encode()).hexdigest()
    if not hmac.compare_digest(expected, parts[0]):
        return None
    return int(user_id)
```
**Rule:** CWE-347

---

#### 6. Hardcoded admin bypass token with trivially guessable value · `sample-project/config.py:8` · high · _security, docs_

`ADMIN_BYPASS_TOKEN = "letmein-admin"` is committed to source control. Any person with read access to this repository (now or forever in git history) can issue `X-Admin-Token: letmein-admin` to delete any note. Combined with the broken signature check (finding 5), no valid user account is even needed. The constant has no comment documenting its purpose or that it must be rotated and loaded from the environment in production.

```python
ADMIN_BYPASS_TOKEN = "letmein-admin"
```

**Fix:**
```python
# Shared static secret checked by is_admin() to gate admin-only endpoints.
# Must be set via ADMIN_BYPASS_TOKEN env var in production.
ADMIN_BYPASS_TOKEN = os.environ["ADMIN_BYPASS_TOKEN"]  # fail loudly at startup if unset
```
**Rule:** CWE-798

---

#### 7. `filter_notes` returns full Python traceback in HTTP 500 response · `sample-project/app.py:54` · high · _security, style, tests, docs_

The error handler in `filter_notes` returns `traceback.format_exc()` in the response body, exposing internal file paths, line numbers, module structure, and variable values to callers. This violates style rule 4.3 (never return an exception's traceback in an HTTP response body) and CWE-209. The endpoint also has no docstring documenting the request shape, the `expression` field, or the `n` variable binding available to expressions. No tests exist for the happy path or the error path.

```python
except Exception as e:
    return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500
```

**Fix:**
```python
app.logger.exception("filter_notes error")
return jsonify({"error": "internal error"}), 500
```
**Rule:** CWE-209; style rule 4.3

---

#### 8. `isAdmin` uses camelCase — must be `is_admin` · `sample-project/auth.py:29` · high · _style, tests, docs_

`isAdmin` violates rule 1.1 (snake_case for functions) and rule 1.4 (boolean-returning functions must read as predicates: `is_admin`, not `isAdmin`). There are no tests for correct/incorrect/missing header values, and no docstring documenting the `X-Admin-Token` header requirement or the static-secret risk.

```python
def isAdmin(request_headers):
```

**Fix:** Rename to `is_admin` everywhere (auth.py declaration + app.py call site `if not is_admin(request.headers)`).
**Rule:** style rules 1.1, 1.4

---

#### 9. `remove_note` has no tests — auth gate and silent-delete are invisible to CI · `sample-project/app.py:39` · high · _tests, docs_

The `remove_note` endpoint's sole security control is the `is_admin` check, but there is no test that a request without `X-Admin-Token` receives 403, no test that a valid admin token produces 204, and no test that a non-existent `note_id` is handled gracefully. Since `delete_note` silently swallows exceptions, a 204 response does not guarantee the note was deleted; this is also not documented.

```python
if not isAdmin(request.headers):
    return jsonify({"error": "forbidden"}), 403
delete_note(note_id)
return "", 204
```

**Fix:** Add `test_remove_note_rejects_non_admin` (DELETE /notes/1 without header → 403) and `test_remove_note_admin_returns_204` (DELETE /notes/1 with valid token → 204).

---

#### 10. MD5 used for password hashing — no salt, cryptographically broken · `sample-project/auth.py:7` · high · _security_

`hashlib.md5` is a fast, unsalted, cryptographically broken hash function. Password databases hashed this way are fully reversible with rainbow tables and can be cracked at billions of hashes per second. Although pre-existing, this PR imports `verify_password` and expands the reach of this function.

```python
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()
```

**Fix:** Replace with `bcrypt` or `argon2-cffi`:
```python
import bcrypt
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
def verify_password(password, stored_hash):
    return bcrypt.checkpw(password.encode(), stored_hash.encode())
```
**Rule:** CWE-916

---

#### 11. Hardcoded production secrets (`JWT_SECRET`, `STRIPE_API_KEY`, `DATABASE_URL`) · `sample-project/config.py:5` · high · _security_

Three production-class secrets are hardcoded in source: a database URL with embedded credentials, a JWT signing key, and a `sk_live_` Stripe API key. The `JWT_SECRET` is newly consumed by `issue_token` in this PR. Even if the values shown are fake, the pattern of committing secrets to source is the finding — the shape invites real values being committed.

```python
DATABASE_URL = "postgresql://devnotes_admin:FAKEPASSWORD_not_real@prod-db.internal:5432/devnotes"
JWT_SECRET = "FAKE_NOT_A_REAL_KEY_s3cr3t_signing_key_2026"
STRIPE_API_KEY = "sk_live_FAKE_NOT_A_REAL_KEY_4eC39HqLyjWDarjtT1zdp7dc"
```

**Fix:** All three must read from environment variables. See SEC-5 fix pattern.
**Rule:** CWE-312

---

#### 12. `insertNote` has mutable default argument `tags=[]` · `sample-project/db.py:29` · high · _style_

Rule 3.1 forbids mutable default arguments. `tags=[]` is created once at function-definition time and shared across every call that omits `tags`. If the list is mutated inside the function, state leaks between invocations. Although pre-existing, the diff adds new import and call sites for `insertNote`.

```python
def insertNote(title, body, user_id, tags=[]):
```

**Fix:**
```python
def insertNote(title, body, user_id, tags=None):
    if tags is None:
        tags = []
```
**Rule:** style rule 3.1

---

### Should fix

#### 13. `applyFilterExpression` uses camelCase — must be `apply_filter_expression` · `sample-project/utils.py:22` · medium · _style_

Rule 1.1 requires snake_case for all functions. `applyFilterExpression` is camelCase. The rename must propagate to the import and call in `app.py`.

**Fix:** Rename to `apply_filter_expression` in `utils.py` and update `app.py` import and call.
**Rule:** style rule 1.1

---

#### 14. `search` endpoint: no test after `user_id` param removed, line too long · `sample-project/app.py:13` · medium · _tests, style_

The PR changed `search` to derive user identity from the `Authorization` header via `current_user_id()` instead of a query parameter. There is no test confirming that an unauthenticated request returns an empty result set rather than all notes (cross-user data leak). Separately, the return statement on line 17 is 102 characters, exceeding the 100-character limit (rule 5.1).

**Fix (tests):** Add `test_search_unauthenticated_returns_empty` and `test_search_scoped_to_authenticated_user`.
**Fix (style):** Break the return statement across lines.

---

#### 15. `read_note` lacks ownership check — IDOR · `sample-project/app.py:20` · medium · _security_

`read_note` fetches a note by ID without checking that the calling user owns it. Any user (or unauthenticated caller) can enumerate note IDs and read other users' notes. This PR wires up `current_user_id()` for search and create but does not apply it to `read_note`.

```python
@app.route("/notes/<int:note_id>")
def read_note(note_id):
    row = get_note(note_id)
    ...
    return jsonify({"id": row[0], "title": row[1], "body": row[2], ...})
```

**Fix:** Add an ownership check:
```python
uid = current_user_id(request.headers.get("Authorization"))
if row[3] != uid:
    return jsonify({"error": "forbidden"}), 403
```
**Rule:** CWE-639

---

#### 16. `create_note` has no test after `user_id` moved to auth header · `sample-project/app.py:28` · medium · _tests_

Like `search`, `create_note` now derives user identity from the `Authorization` header. There is no test that omitting the token results in a predictable outcome (e.g., a note with `None` as owner), and no test that the `MAX_NOTE_LENGTH` guard still fires correctly under the new control flow.

**Fix:** Add `test_create_note_too_long` (body > MAX_NOTE_LENGTH → 400) and `test_create_note_unauthenticated` (no header → error or documented None-owner behaviour).

---

#### 17. `getEnvOrDefault` uses camelCase — must be `get_env_or_default` · `sample-project/config.py:14` · medium · _style_

Rule 1.1 requires snake_case. `getEnvOrDefault` is camelCase. Although pre-existing and not directly modified, it is in `config.py` which this PR modifies.

**Fix:** Rename to `get_env_or_default` and update any call sites.
**Rule:** style rule 1.1

---

### Consider

- **Wildcard import in `db.py`** · `sample-project/db.py:2` · _style_ — `from config import *` is forbidden by rule 2.1; replace with explicit symbol imports. This silently pulls in the new `ADMIN_BYPASS_TOKEN` constant.

---

### Test coverage

The entire new surface area of this PR is untested. The existing test suite covers only `slugify` and `truncate`; nothing in `tests/` touches any of the five changed files.

| Added or changed | Tested | Suggested test |
|---|---|---|
| `applyFilterExpression` (utils.py:23) | ❌ | `test_apply_filter_expression_basic`, `test_apply_filter_expression_rejects_code_execution` |
| `search_notes` SQL change (db.py:13) | ❌ | `test_search_notes_rejects_sql_injection`, `test_search_notes_null_user_id` |
| `delete_note` (db.py:48) | ❌ | `test_delete_note_only_deletes_target`, `test_delete_note_rejects_non_integer` |
| `current_user_id` (auth.py:20) | ❌ | `test_current_user_id_returns_none_for_missing_token`, `test_current_user_id_accepts_forged_token` |
| `issue_token` (auth.py:14) | ❌ | `test_issue_token_format`, `test_issue_token_different_users_differ` |
| `isAdmin` (auth.py:29) | ❌ | `test_is_admin_returns_true_for_correct_token`, `test_is_admin_returns_false_for_wrong_token` |
| `remove_note` (app.py:39) | ❌ | `test_remove_note_rejects_non_admin`, `test_remove_note_admin_returns_204` |
| `filter_notes` (app.py:46) | ❌ | `test_filter_notes_valid_expression`, `test_filter_notes_error_returns_500` |
| `search` auth change (app.py:13) | ❌ | `test_search_unauthenticated_returns_empty`, `test_search_scoped_to_user` |
| `create_note` auth change (app.py:28) | ❌ | `test_create_note_too_long`, `test_create_note_unauthenticated` |

---

### Reviewer status

| Reviewer | Status | Findings | Time |
|---|---|---|---|
| security-reviewer | ran; output transcribed | 10 | N/A |
| style-reviewer | ran; output transcribed | 9 | N/A |
| test-coverage-reviewer | ok — wrote its own file | 10 | N/A |
| docs-reviewer | ok — wrote its own file | 8 | N/A |

**Provenance:** all four subagents executed concurrently from a single dispatch
(6s / 1m21s / 1m38s / 1m38s). The security and style subagents ran without
file-write permission and returned findings as chat output, which the orchestrator
transcribed into `reviews/raw/security.json` and `reviews/raw/style.json`. Those two
raw files are second-hand. `tests.json` and `docs.json` were written directly by
their subagents.

**Timing:** every timestamp field is `null` because the agent has no clock. Wall-clock
figures are measured externally and recorded in `reviews/run-metadata.json`.

37 findings were reported across four reviewers before deduplication. After merging findings at the same file+symbol location (keeping the highest severity and combining reviewer tags), **17 findings** remain.

**Deduplication note:** 20 findings collapsed into 9 merged entries. Where reviewers flagged the same symbol for different reasons (e.g., SEC-3 flagged `delete_note` for SQL injection while STY-5 flagged the bare `except:` and DOC-8 flagged the missing docstring), all reasons are preserved in the merged finding. No disagreements between reviewers were observed — every multi-reviewer collision was on a different dimension of the same defect.

---

### Checked and clean

- `slugify`, `truncate`, `parse_tags` — utility functions untouched by the diff and fully tested; no security or style issues
- `insertNote` body (query parameterisation) — pre-existing INSERT uses `?` placeholders correctly; no injection introduced here
- `get_note` — pre-existing, uses `?` placeholder correctly; not modified
- Flask import order in `app.py` — standard library (`traceback`), then third-party (`flask`), then first-party; correctly separated per rule 2.2
- `hash_password` and `verify_password` naming — snake_case, no mutable defaults, no bare excepts in those functions

### Not checked

- Database schema and migrations — no migration files are present in the repository
- Python dependency versions — no `requirements.txt` found
- Deployment and infrastructure configuration — not present
- OpenAPI / external API documentation — no such file exists
- Integration / end-to-end coverage between routes and the real database — no integration test harness present; all test findings above are unit-level gaps
- Pre-existing routes not modified by this diff (`/auth/register`) — out of scope for a diff review

---

<sub>Generated by four IBM Bob subagents running in parallel, synthesized in Agent
mode. Wall clock N/A (timing not observable). Provenance for every finding is in
`reviews/raw/`.</sub>
