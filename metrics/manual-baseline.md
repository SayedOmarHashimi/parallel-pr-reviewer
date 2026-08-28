# Manual review baseline — protocol and worksheet

The "before" half of the impact claim. Everything Bob's numbers are compared
against comes from this sheet, so the protocol matters more than the result.

---

## Who should do this

**Not you.** You already know several of the planted defects from building the
fixture. A reviewer who knows the answers is not a baseline.

Recruit **one person** who has never seen this repository: a classmate, a
roommate who codes, anyone in the hackathon Slack. Some Python familiarity is
enough — this is a 67-line diff, not a systems audit.

If you genuinely cannot find anyone, see *Fallback* at the bottom. Do not quietly
review it yourself and present it as a cold baseline.

## What the reviewer gets

Give them exactly this, and nothing else:

1. The PR on GitHub — https://github.com/SayedOmarHashimi/parallel-pr-reviewer/pull/1
   (or `pr/PR-1.diff` locally)
2. The PR description
3. `bob-config/style-guide.md` — they should review against the same rules the
   style subagent uses, or the comparison is unfair to the human
4. This worksheet, from "Findings" down

**Do not give them:** `metrics/answer-key.md`, anything in `bob-config/subagents/`,
or any hint about how many issues exist. Do not tell them the point is to test an
AI — that changes how hard people look.

## What to tell them

> "Review this pull request the way you'd review a teammate's. Check whether it's
> secure, whether it follows the style guide, whether it's tested, and whether
> it's documented. Write down everything you'd flag. Start a timer when you open
> the diff and stop it when you'd be ready to submit the review. Work at your
> normal pace — don't rush and don't go deeper than you normally would."

Then leave them alone. Do not hover, do not hint, do not answer "is this
intentional?" — say "review it however you'd review it."

## Findings

Reviewer: ______________  Date: __________
Timer start: ________  Timer stop: ________  **Elapsed: ________**

| # | File | Line | What you'd flag |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| 6 | | | |
| 7 | | | |
| 8 | | | |

Anything you noticed but decided not to flag:

_______________________________________________

---

## Scoring (you do this afterward, not the reviewer)

Match each finding against `metrics/answer-key.md`, diff-scoped rows only
(S4 S5 S6 S8 S9 S10 S11 S13, C3 C4, T1 T2, D1 — **13 planted**).

| | Count |
|---|---|
| Elapsed time | |
| Findings that match a planted defect | |
| Findings that are real but not on the list (**credit these**) | |
| False positives | |
| **Planted defects caught, of 13** | |

Rules for scoring honestly:

- **Credit real findings that aren't on my list.** If they spot something genuine
  I didn't plant, it counts for the human. The answer key is not exhaustive.
- **"Missing tests" as one line counts as one finding**, not two. Score the same
  way you score Bob — the orchestrator dedupes, so the human gets the same grace.
- **Vague doesn't count.** "Auth looks sketchy" is not a finding. "Line 21 trusts
  the user id without verifying the hash" is.
- Record the elapsed time **as measured**, even if they finished in 8 minutes.

## Fallback if you truly cannot recruit anyone

Do **not** fabricate a baseline. Instead, change what you claim. Drop the
"human found N" comparison entirely and make the impact claim about what you can
measure without a second person:

- Wall-clock time for a complete four-concern review (from `run-metadata.json`)
- Coverage against the catalogued defect list — Bob caught X of 13, an audited
  denominator
- Consistency: the same four passes run every time, with no concern dropped under
  deadline pressure

That is a weaker headline but it is fully defensible, and "we measured what we
could measure honestly" survives a judge's follow-up question. An invented human
baseline does not.
