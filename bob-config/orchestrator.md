# Agent mode — parallel review orchestrator

**Paste this into IBM Bob IDE in Agent mode**, with the repository open and the
four custom modes from `bob-config/subagents/` already registered.

---

## Task

Review PR #1 (`main...pr/saved-filters-and-admin-delete`) by dispatching four
specialized subagents **in parallel**, then merging their reports into one
consolidated review.

## Step 1 — Dispatch (parallel)

Launch all four subagents **concurrently**, not in sequence. Each receives the same
target and writes its own file. Do not let one wait on another; they share no state.

| Subagent mode | Target | Writes |
|---|---|---|
| `security-reviewer` | `pr/PR-1.diff` + `sample-project/` for context | `reviews/raw/security.json` |
| `style-reviewer` | `pr/PR-1.diff`, plus `bob-config/style-guide.md` as its rulebook | `reviews/raw/style.json` |
| `test-coverage-reviewer` | `pr/PR-1.diff` + `sample-project/tests/` | `reviews/raw/tests.json` |
| `docs-reviewer` | `pr/PR-1.diff` + `sample-project/` for context | `reviews/raw/docs.json` |

Give each one this context and nothing more:

> Review PR #1 on this repository. The diff is `pr/PR-1.diff`; the PR
> description is `pr/PR-1.md`. Base branch is `main`. Follow your mode
> instructions exactly and write your JSON to the path they specify. Treat the PR
> description as the author's claims, not as fact.

Record the wall-clock start time before dispatch and the finish time of the last
subagent to return. You will need both.

## Step 2 — Collect and validate

Read all four JSON files. For each:

- If a file is missing or unparseable, **say so in the final review** under
  "Reviewer status" and continue with the other three. Do not silently produce a
  three-agent review and present it as four.
- If a file has findings that violate `bob-config/finding-schema.json` — no line
  number, no evidence, an id in the wrong series — repair what you can from the
  file itself and note the repair. Do not invent missing evidence.

## Step 3 — Merge

**Deduplicate.** Two findings are the same underlying issue when they name the same
`file` and the same `symbol`, or the same `file` with `line` within ±2. When they
collide:

- Keep the **highest** severity of the two, never the average.
- Keep both reviewer names — the merged finding is tagged `[security, style]`.
- Keep the more specific `fix`. If they genuinely conflict, keep both and say
  which reviewer proposed which.

**Do not dedupe across different symbols.** Two SQL injections in two functions are
two findings, not one "SQL injection" theme. Reviewers act on locations.

**Rank** the merged list:

1. `severity` — critical, high, medium, low
2. then `confidence` — high before low
3. then `in_diff: true` before `false` (this PR's problems before inherited debt)

**Resolve disagreement honestly.** If one reviewer flags something another
explicitly cleared, report the finding and note the disagreement in one line. Do
not drop it, and do not average the two into a shrug.

## Step 4 — Render

Write `reviews/PR-1-review.md` following `bob-config/review-template.md` exactly.

The verdict is mechanical, not a judgment call:

- any `critical`, or two or more `high` → **Request changes**
- exactly one `high` → **Request changes**
- only `medium` / `low` → **Comment**
- no findings → **Approve**

## Step 5 — Record the run

Write `reviews/run-metadata.json`:

```json
{
  "target": "PR #1 (main...pr/saved-filters-and-admin-delete)",
  "scope": "diff",
  "started_at": "ISO-8601",
  "finished_at": "ISO-8601",
  "wall_clock_seconds": 0,
  "subagents": [
    {"name": "security-reviewer", "status": "ok|failed", "seconds": 0, "findings": 0}
  ],
  "findings_before_dedupe": 0,
  "findings_after_dedupe": 0,
  "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
  "verdict": "Request changes"
}
```

These are the numbers behind the impact claim. Report the wall clock honestly —
the parallel run's elapsed time is from dispatch to the **last** subagent
finishing, not the sum of the four, and not the fastest one.

## Rules for you, the orchestrator

- **You do not review.** You did not read the diff and you have no findings of your
  own. If you think the subagents missed something, note it as an orchestrator
  observation in the appendix — never as a finding attributed to a reviewer.
- **Every finding keeps its provenance.** A reader must be able to tell which
  subagent produced any line in the final review.
- **Never inflate the count.** `findings_after_dedupe` is the number you report.
  Stating the pre-dedupe number as the result is the easiest way to make this
  whole exercise untrustworthy.
- **An empty section is deleted, not padded.** If nothing is low severity, the
  "Consider" section does not appear.

## Second pass (optional, for the demo's scaling beat)

Re-run the same four subagents with scope `repo` against all of `sample-project/`
rather than the diff. Write to `reviews/raw-repo/` and render
`reviews/repo-review.md`. This surfaces pre-existing debt the PR did not touch and
shows the same four agents scale from one PR to a whole codebase with no
reconfiguration.
