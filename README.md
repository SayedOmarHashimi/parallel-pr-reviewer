# Parallel PR Reviewer — powered by IBM Bob 2.0

> IBM TechXchange 2026 Pre-conference Dev Day Hackathon submission
> Theme: *Build with purpose using IBM Bob 2.0* · Workflow: **code review**

---

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

<!-- filled in after the Bob run — see metrics/ -->
| | Manual review | Bob parallel review |
|---|---|---|
| Wall-clock time | _TBD_ | _TBD_ |
| Defects written up (of 13 catalogued in the diff) | _TBD_ | _TBD_ |
| Prior knowledge of the defects | _see below_ | none |

The manual baseline protocol, including how the reviewer's prior knowledge is
accounted for, is in [`metrics/manual-baseline.md`](metrics/manual-baseline.md).
Defects are scored against an audited list of 13 in the PR diff.

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
