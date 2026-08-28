# PR #1 — Add saved filters and admin note deletion

**Branch:** `pr/saved-filters-and-admin-delete` → `main`
**Author:** @devnotes-contributor
**Files changed:** 5 · +67 −9

## What this does

Customers asked for two things this sprint:

1. **Saved filters.** `POST /notes/filter` accepts a filter expression and returns
   the caller's matching notes. Expressions are simple Python-ish predicates so
   power users can write whatever they want without us shipping a query language.
2. **Admin deletion.** `DELETE /notes/<id>` lets support staff remove abusive
   notes. Gated behind the `X-Admin-Token` header.

It also wires up real token auth — `search` and `create` previously took
`user_id` as a plain request parameter, which was obviously temporary. Now the
caller identity comes from the `Authorization` header via `current_user_id()`.

## Testing

Ran the existing suite locally, all green. Endpoints smoke-tested by hand with
curl. Happy to add integration tests in a follow-up if reviewers want them —
wanted to get this in before the release cut.

## Notes for reviewers

Search now interpolates the query into the LIKE clause so we can support the
`%` wildcard that users kept asking for.
