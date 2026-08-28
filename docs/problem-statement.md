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

This is a poor fit for one reviewer and a good fit for four specialists — which
teams don't staff, because it isn't economically possible.

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
numbered policy document in the repository — and cites the clause it enforces on
every finding. Swapping in another team's guide changes its behavior with no
prompt edits.

All four emit findings against one JSON schema. Bob's Agent mode merges them:
deduplicating issues found by more than one reviewer, ranking by severity, and
preserving which subagent produced each finding. The output pastes directly into
GitHub.

### Measured impact

Against a 67-line pull request containing {{PLANTED}} independently catalogued
defects:

| | Manual review | Bob parallel review |
|---|---|---|
| Wall clock | {{MANUAL_MINUTES}} min | {{BOB_TIME}} |
| Defects written up | {{MANUAL_FOUND}} of {{PLANTED}} | {{BOB_FOUND}} of {{PLANTED}} |
| Prior knowledge of the defects | full | none |

The manual pass was run by the fixture's author, who knew every defect in advance
— making its time a floor rather than an average, and its find count a ceiling.
Both biases run against the tool being measured.

The expensive defects are the ones that don't look like defects: a token whose
user identity is trusted without verification, and a docstring promising security
properties the function never implements. Neither is visible to a linter.

The architecture scales without reconfiguration: the same subagents run against a
whole repository instead of a diff, and adding a fifth concern — accessibility,
licensing, performance — means one more mode definition, not a redesign.

SUBMIT>>>
