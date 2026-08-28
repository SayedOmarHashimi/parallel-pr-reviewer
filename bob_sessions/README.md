# Bob task session evidence

Frames captured from a screen recording of the submission run (run 3,
2026-08-28 15:55:01–16:02:34), extracted at full 2880×1800 resolution.

| File | What it shows |
|---|---|
| `01-new-task-fresh-context.png` | A new Bob task starting with clean context — no carry-over from earlier runs |
| `02-parallel-run.png` | **The key frame.** All four subagent cards from a single dispatch: 6s / 1m21s / 1m38s / 1m38s |
| `02b-parallel-run-alt.png` | Alternate from an earlier run: all four cards reading `Running · 31s` simultaneously |
| `03-subagents-dispatched.png` | Agent mode dispatching the four reviewers |
| `04-agent-mode-merge.png` | Agent mode merging the four JSON reports |
| `05-render-and-verdict.png` | Severity breakdown and the mechanical verdict |
| `06-run-complete.png` | Run complete: verdict, both output files written, all four raw JSONs in the explorer |

## Still to capture manually

- [ ] `00-modes-registered.png` — Bob Settings → Modes, showing the four Workspace-scope
      reviewers alongside the three built-ins. Take this from the live UI; it never
      appeared in the recording.
- [ ] `07-final-review.png` — `reviews/PR-1-review.md` open in **rendered markdown
      preview**, not raw source.

## Before publishing any screenshot

Check it shows no account email, API key, or token. `06-run-complete.png` was
checked and is clean; the Bob Settings *page* does display the account email, so
do not capture that screen.

## Note on provenance

All four subagents executed concurrently from one dispatch. Two of them
(security, style) ran without file-write permission and returned findings as chat
output, which the orchestrator transcribed into `reviews/raw/`. This is disclosed
in `reviews/run-metadata.json` and in the Reviewer status table of the review.
