# Parallel PR Reviewer — powered by IBM Bob 2.0

> IBM TechXchange 2026 Pre-conference Dev Day Hackathon submission
> Theme: *Build with purpose using IBM Bob 2.0* · Workflow: **code review**
>
> **▶ [Watch the 3-minute demo](https://youtu.be/UJ7Fsj9TeFs)**

---

## Start here

| What | Where |
|---|---|
| The pull request being reviewed | [PR #1](https://github.com/SayedOmarHashimi/parallel-pr-reviewer/pull/1) (5 files, 67 added, 9 removed) |
| Bob's consolidated review of it | [`reviews/PR-1-review.md`](reviews/PR-1-review.md) |
| The four subagent definitions | [`bob-config/subagents/`](bob-config/subagents) |
| The orchestration prompt | [`bob-config/orchestrator.md`](bob-config/orchestrator.md) |
| Evidence of Bob usage | [`bob_sessions/`](bob_sessions) |
| How the timings were measured | [`reviews/run-metadata.json`](reviews/run-metadata.json) |

Note on branches: `main` holds the codebase **before** the pull request. The changes
under review live on the `pr/saved-filters-and-admin-delete` branch, which is what
PR #1 shows. That is what gives the reviewers a real diff to work from.

## The problem

Reviewing a pull request means checking four unrelated concerns — **security**,
**style/convention**, **test coverage**, and **documentation** — and a human does
them *sequentially*, in one head, under time pressure. That takes 20–40 minutes per
PR, and the concern checked last is the one that gets skimmed.

## The solution

Split the review into four specialized IBM Bob **subagents** that run **in parallel**,
each with a single job and its own rules file, then use Bob's **Agent mode** to
synthesize their four reports into one consolidated, paste-ready PR review.

| Subagent | Job |
|---|---|
| `security-reviewer` | Hardcoded secrets, injection risks, unsafe patterns |
| `style-reviewer`    | Violations of the project style guide (`bob-config/style-guide.md`) |
| `test-reviewer`     | Changed code paths with no corresponding test |
| `docs-reviewer`     | Missing/misleading docstrings on public functions |

## Measured impact

Reviewing PR #1 — 5 files, +67 −9 — for four concerns at once:

| | Measured |
|---|---|
| Four specialist reviews, dispatched together | **98 seconds** |
| Full consolidated review, prompt to finished file | **6 min 12 s** |
| Findings raised | 37 raw → **17** after merge |
| Severity | 4 critical · 8 high · 4 medium · 1 low |
| Verdict | Request changes |

The four critical findings are each independently a merge blocker: remote code
execution via `eval()` on a request body, a parameterised SQL query deliberately
rewritten into string interpolation, an authentication token whose user identity is
never verified against its signature, and a second SQL injection in the delete path.

Two of those are near-invisible to a skimming reviewer. The token bug is four lines
that look like ordinary parsing. And one documentation finding is not a *missing*
docstring but a false one — it promises a signed JWT expiring in 24 hours, and the
function neither signs nor expires anything.

**How these numbers were obtained.** Bob has no wall clock; it reports `null` for
every timestamp rather than inventing one. All timings here are measured externally
from artifact modification times and a screen recording, and are recorded with their
method in [`reviews/run-metadata.json`](reviews/run-metadata.json). Finding counts
are Bob's own, and both the pre-merge (37) and post-merge (17) figures are published
so the merge is auditable.

No human-baseline comparison is claimed here, because none was measured.

## Repository layout

```
sample-project/   Deliberately imperfect codebase under review (the fixture)
bob-config/       Subagent role definitions + style guide pasted into Bob IDE
reviews/          Consolidated review output produced by Bob
metrics/          Manual-baseline vs Bob timing and issue counts
docs/             Submission deliverables (problem statement, Bob usage, demo script)
bob_sessions/     Bob IDE task session screenshots — evidence of Bob usage
```

## How to reproduce

1. Open this repo in **IBM Bob IDE 2.0**.
2. Register the four subagents from `bob-config/` (see `bob-config/README.md`).
3. Run the orchestration prompt in Agent mode against the PR diff in `sample-project/`.
4. Bob writes the consolidated review to `reviews/`.

## Data & credentials

- No client data, no personal data, no scraped social media data. The reviewed
  codebase is synthetic and written for this submission.
- Any secret-looking string inside `sample-project/` is **fake, planted fixture
  data** for the security subagent to find — see `sample-project/README.md`.
- Real credentials are excluded via `.gitignore` and `.bobignore`.
