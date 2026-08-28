# Planted issue answer key — DO NOT LET BOB READ THIS

Listed in `.bobignore`. It exists so you can score Bob's recall honestly
(caught / planted) and so the README impact table is defensible rather than vibes.

**24 issues planted.** The `Scope` column matters:

- **PR** — introduced or modified by PR #42. A diff-scoped review should catch these.
- **repo** — pre-existing on `main`. Only a whole-repo scan finds these.

That split is itself a demo beat: run the subagents against the diff, then against
the repo, and show the second pass surfacing debt the PR didn't touch.

## Security (13)

| # | Scope | File | Symbol | Issue |
|---|---|---|---|---|
| S1 | repo | config.py | `DATABASE_URL` | DB password hardcoded in source |
| S2 | repo | config.py | `JWT_SECRET` | Signing secret hardcoded in source |
| S3 | repo | config.py | `STRIPE_API_KEY` | Third-party API key hardcoded in source |
| S4 | **PR** | config.py | `ADMIN_BYPASS_TOKEN` | Static shared admin secret in source |
| S5 | **PR** | db.py | `search_notes` | **Regression.** `main` used a parameterized query; this PR replaces it with an f-string → SQL injection. The PR description even brags about it ("interpolates the query into the LIKE clause"). |
| S6 | **PR** | db.py | `delete_note` | SQL injection — f-string interpolates `note_id` |
| S7 | repo | auth.py | `hash_password` | Unsalted MD5 for password storage |
| S8 | **PR** | auth.py | `issue_token` | Homemade token, SHA-1, unsigned, never expires |
| S9 | **PR** | auth.py | `current_user_id` | **Critical.** Trusts the user id appended to the token; the hash half is never verified. Any client sets any id and impersonates any user. |
| S10 | **PR** | auth.py | `isAdmin` | Non-constant-time comparison against a static token |
| S11 | **PR** | utils.py | `applyFilterExpression` | **Critical.** `eval()` on request body → remote code execution |
| S12 | repo | app.py | `read_note` | IDOR — no ownership check; any user reads any note |
| S13 | **PR** | app.py | `filter_notes` | Stack trace + exception text returned to the client |

*Bonus find (not one of the 24): `app.run(host="0.0.0.0", debug=True)` exposes the
Werkzeug debugger.*

## Style / convention (6)

| # | Scope | File | Symbol | Issue |
|---|---|---|---|---|
| C1 | repo | config.py | `getEnvOrDefault` | camelCase; project standard is snake_case |
| C2 | repo | db.py | `insertNote` | camelCase |
| C3 | **PR** | auth.py | `isAdmin` | camelCase |
| C4 | **PR** | utils.py | `applyFilterExpression` | camelCase |
| C5 | repo | db.py | line 2 | `from config import *` wildcard import |
| C6 | repo | db.py | `insertNote` | Mutable default argument `tags=[]` |

*Bonus: bare `except: pass` in `delete_note` (PR scope) — swallows errors silently.
Score it under whichever category Bob files it; style and security both own it.*

## Test coverage (3)

| # | Scope | Target | Issue |
|---|---|---|---|
| T1 | **PR** | `auth.py` | The PR adds three auth functions and zero tests. Nothing verifies token issue, identity parsing, or the admin check. |
| T2 | **PR** | `delete_note`, `/notes/filter`, `/notes/<id>` DELETE | New code paths, no tests. The PR says "happy to add integration tests in a follow-up." |
| T3 | repo | `utils.py` | `parse_tags` untested; `truncate` only exercises the short-text branch — the branch that actually truncates never runs. |

## Documentation (2)

| # | Scope | File | Symbol | Issue |
|---|---|---|---|---|
| D1 | **PR** | auth.py | `issue_token` | **Docstring is factually false** — claims a signed JWT valid 24 hours. Neither signed nor expiring. Worse than no docstring, and a grep-for-missing-docstrings reviewer will not catch it. |
| D2 | mixed | db.py, auth.py, utils.py, app.py | many | Public functions with no docstring: `search_notes`, `insertNote`, `delete_note`, `hash_password`, `verify_password`, `current_user_id`, `isAdmin`, `parse_tags`, `applyFilterExpression`, `getEnvOrDefault`, and every route handler. No module docstrings outside `config.py`. |

---

## Scoring sheet

Fill in after the Bob run.

**Diff-scoped pass** (PR #42 only — 13 planted: S4 S5 S6 S8 S9 S10 S11 S13, C3 C4, T1 T2, D1)

| Category | Planted | Manual review caught | Bob caught |
|---|---|---|---|
| Security | 8 | | |
| Style | 2 | | |
| Tests | 2 | | |
| Docs | 1 | | |
| **Total** | **13** | | |

**Whole-repo pass** (all 24)

| Category | Planted | Bob caught |
|---|---|---|
| Security | 13 | |
| Style | 6 | |
| Tests | 3 | |
| Docs | 2 | |
| **Total** | **24** | |

Also record: **false positives** (findings not on this list that aren't real
problems), and **wall-clock time** for the manual baseline vs the Bob run.
