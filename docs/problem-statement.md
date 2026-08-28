# Written statement 1 — Problem & Solution

**Limit: 500 words.** Only the text between the `<<<SUBMIT` markers is submitted.
Everything outside them is working notes.

Fill `{{...}}` from `reviews/run-metadata.json` and your scored manual baseline.
Word count is checked after substitution — the placeholders are shorter than the
numbers replacing them, so re-count before pasting.

<<<SUBMIT

## Parallel PR Reviewer

### The problem

Reviewing a pull request is not one task. It is four unrelated ones — is this
secure, does it follow our conventions, is it tested, is it documented — and a
human performs them sequentially, in a single head, under deadline pressure. A
careful review of even a small PR takes 20 to 40 minutes.

The cost is not only time. Attention degrades across the four passes. The concern
checked last is the one that gets skimmed, and which concern comes last depends on
nothing more principled than what the reviewer noticed first. Security review, the
one with the worst failure mode, is routinely the pass that gets cut when the
release is waiting.

This is a poor fit for one reviewer and an excellent fit for four specialists. Teams
don't staff four specialists per PR because it is not economically possible.

### The solution

Parallel PR Reviewer splits a single code review into four IBM Bob subagents that
run concurrently against the same diff, each with a narrow mandate and an explicit
list of concerns that are *not* its job:

- **security-reviewer** — injection, hardcoded credentials, authentication and
  authorization defects, weak cryptography, information disclosure, and removed
  protections
- **style-reviewer** — violations of the team's written style guide
- **test-coverage-reviewer** — changed behavior with no test that would fail if it broke
- **docs-reviewer** — missing documentation, and documentation that is actively wrong

The style reviewer carries no built-in rules. It reads the team's style guide — a
real, numbered policy document in the repository — and must cite the clause it is
enforcing on every finding. Swapping in a different team's guide changes the
agent's behavior with no prompt changes.

All four emit findings against one JSON schema. Bob's Agent mode then merges them:
deduplicating issues found by more than one reviewer, ranking by severity, and
preserving which subagent produced each finding. The output is a consolidated
review formatted to paste directly into GitHub.

### Measured impact

Against a 67-line pull request containing {{PLANTED}} independently catalogued
defects:

| | Manual review | Bob parallel review |
|---|---|---|
| Wall clock | {{MANUAL_MINUTES}} min | {{BOB_TIME}} |
| Defects found | {{MANUAL_FOUND}} | {{BOB_FOUND}} |

The findings the manual pass missed were the expensive kind: an authentication
token whose user identity is trusted without verification, and a docstring
promising security properties the function does not implement. Neither is visible
to a linter; both look like ordinary code.

The architecture scales without reconfiguration. The same four subagents run
against a full repository instead of a diff, and adding a fifth concern —
accessibility, licensing, performance — means writing one more mode definition, not
redesigning the review.

SUBMIT>>>
