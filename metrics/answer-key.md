# Planted issue answer key — DO NOT LET BOB READ THIS

This file is listed in `.bobignore`. It exists so you can score Bob's recall
honestly (findings caught / findings planted) and so the numbers in the README
impact table are defensible rather than vibes.

**24 issues planted across 4 categories.**

## Security (13)

| # | File | Symbol | Issue |
|---|---|---|---|
| S1 | config.py | `DATABASE_URL` | Production DB password hardcoded in source |
| S2 | config.py | `JWT_SECRET` | Signing secret hardcoded in source |
| S3 | config.py | `STRIPE_API_KEY` | Third-party API key hardcoded in source |
| S4 | config.py | `ADMIN_BYPASS_TOKEN` | Static shared admin secret in source |
| S5 | db.py | `search_notes` | SQL injection — f-string interpolates `query` and `user_id` |
| S6 | db.py | `delete_note` | SQL injection — f-string interpolates `note_id` |
| S7 | auth.py | `hash_password` | Unsalted MD5 for password storage |
| S8 | auth.py | `issue_token` | Homemade token, SHA-1, no signature, never expires |
| S9 | auth.py | `current_user_id` | **Critical.** Trusts the user id appended to the token — client can set any id and impersonate any user. No verification of the hash half. |
| S10 | auth.py | `isAdmin` | Non-constant-time comparison against a static token |
| S11 | utils.py | `applyFilterExpression` | **Critical.** `eval()` on request body → remote code execution |
| S12 | app.py | `read_note` | IDOR — no ownership check; any user reads any note |
| S13 | app.py | `filter_notes` | Stack trace + exception text returned to the client |

*(Also worth catching: `app.run(host="0.0.0.0", debug=True)` — Werkzeug debugger
exposed. Count it as a bonus find, not one of the 24.)*

## Style / convention (6)

| # | File | Symbol | Issue |
|---|---|---|---|
| C1 | config.py | `getEnvOrDefault` | camelCase; project standard is snake_case |
| C2 | db.py | `insertNote` | camelCase |
| C3 | auth.py | `isAdmin` | camelCase |
| C4 | utils.py | `applyFilterExpression` | camelCase |
| C5 | db.py | line 2 | `from config import *` wildcard import |
| C6 | db.py | `insertNote` | Mutable default argument `tags=[]` |

*(Bonus: bare `except: pass` in `delete_note` — swallows errors silently. Score it
under whichever category Bob files it; both style and security defensibly own it.)*

## Test coverage (3)

| # | Target | Issue |
|---|---|---|
| T1 | `auth.py` | Zero tests. Password hashing, token issue, and admin check all unverified. |
| T2 | `db.py` + all `app.py` routes | Zero tests. No route is exercised. |
| T3 | `utils.py` | `parse_tags` and `applyFilterExpression` untested; `truncate` only exercises the short-text branch, never the branch that actually truncates. |

## Documentation (2)

| # | File | Symbol | Issue |
|---|---|---|---|
| D1 | auth.py | `issue_token` | **Docstring is factually false** — claims a signed JWT valid 24 hours. It is neither signed nor expiring. Worse than no docstring. |
| D2 | db.py, auth.py, utils.py, app.py | many | Public functions without docstrings: `search_notes`, `insertNote`, `delete_note`, `hash_password`, `verify_password`, `current_user_id`, `isAdmin`, `parse_tags`, `applyFilterExpression`, `getEnvOrDefault`, and every route handler. No module docstrings outside `config.py`. |

---

## Scoring sheet

Fill in after the Bob run:

| Category | Planted | Manual review caught | Bob caught |
|---|---|---|---|
| Security | 13 | | |
| Style | 6 | | |
| Tests | 3 | | |
| Docs | 2 | | |
| **Total** | **24** | | |

Also record: false positives Bob reported (findings not on this list that aren't
real), and wall-clock time for each run.
