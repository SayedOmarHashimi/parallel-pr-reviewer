# Video demo script — Parallel PR Reviewer

**Hard limit: 3:00.** Target 2:52 so an upload re-encode can't push you over.
Requirement: 90+ seconds of the solution working live, narrated, with Bob visibly
doing the work.

---

## ⚠️ Numbers to fill before recording

Every `{{...}}` below comes from a real run. Do not estimate any of them on camera.

| Placeholder | Source |
|---|---|
| `{{MANUAL_MINUTES}}` | Your timed manual review of `pr/PR-42.diff` |
| `{{MANUAL_FOUND}}` | Issues you found manually, scored vs `metrics/answer-key.md` |
| `{{BOB_TIME}}` | `run-metadata.json` → `wall_clock_seconds` |
| `{{BOB_FOUND}}` | `run-metadata.json` → `findings_after_dedupe` |
| `{{PLANTED}}` | 13 (diff-scoped) — already known |
| `{{CRITICAL_NAME}}` | The critical finding you'll spotlight (expected: the token identity bug) |

If Bob finds fewer than you did manually, **say that instead**. A demo that reports
a real mixed result is more credible than one that reports a suspiciously clean
sweep, and judges scoring "effectiveness" have seen a lot of the latter.

---

## Pre-record checklist

- [ ] Bob IDE at **160%+ zoom**. Judges watch this in a small embedded player.
- [ ] Editor theme: high contrast. Default dark themes lose thin syntax colors on re-encode.
- [ ] Close every unrelated panel, tab, notification, and Slack.
- [ ] `reviews/raw/` **emptied** — the files must appear on camera, not sit there pre-made.
- [ ] `pr/PR-42.diff`, `orchestrator.md`, and the Modes panel each pre-opened in a tab so you never hunt for a file mid-take.
- [ ] Screen recording at 1080p minimum.
- [ ] **Scrub for credentials:** no IBM Cloud account id, no API key, no email in any visible panel, title bar, or notification.
- [ ] Do a silent dry run of the click path once. The demo must not be the first time you click it.

---

## Script

### 0:00 – 0:20 · The problem (20s)

**On screen:** `pr/PR-42.diff` open, scrolling slowly.

> "This is a 67-line pull request. To review it properly I have to check four
> different things — is it secure, does it follow our style guide, is it tested,
> is it documented. I check them one after another, in my head, and by the fourth
> one I'm skimming. That's twenty to forty minutes, and the last thing I check is
> the thing I miss."

---

### 0:20 – 0:35 · The idea (15s)

**On screen:** Bob IDE **Modes** panel — all four custom modes visible.

> "So I built four specialists in IBM Bob. Security, style, test coverage, docs.
> Each one has a single job and an explicit list of things that are not its job.
> And instead of running one after another — they run at the same time."

---

### 0:35 – 2:35 · Live demo (120s)

#### 0:35 – 0:50 · Dispatch

**On screen:** Agent mode. Paste `bob-config/orchestrator.md`. Press enter. **Start a visible timer.**

> "One prompt in Agent mode dispatches all four against this PR."

#### 0:50 – 1:15 · The parallel run — *this is the shot that matters*

**On screen:** Bob **Tasks panel**, four tasks running concurrently. Hold on it. Let it breathe.

> "Four subagents, four tasks, running in parallel — not queued. Each one is
> reading the same diff from a completely different angle. The style reviewer
> isn't guessing at conventions either; it's reading our actual style guide, a
> real document in the repo, and it has to cite the clause number on every
> finding."

**Cut to** `bob-config/style-guide.md` for ~3 seconds, then back to Tasks.

#### 1:15 – 1:35 · Structured output

**On screen:** `reviews/raw/` — four JSON files appearing. Open `security.json` briefly.

> "Each one writes structured JSON against a shared schema. Severity, file, line,
> evidence, and a fix — not prose. That's what makes the next step possible."

#### 1:35 – 1:55 · Synthesis

**On screen:** Agent mode merging; `reviews/PR-42-review.md` being written.

> "Then Agent mode merges all four. It deduplicates — two reviewers flagged the
> same swallowed exception — ranks by severity, and every finding keeps the name
> of the subagent that found it."

#### 1:55 – 2:25 · The findings — *land the specific one*

**On screen:** `PR-42-review.md`, scroll to the top finding, then to the docs finding.

> "Here's the one I want to show you. This PR adds token authentication. The token
> is a hash, then a dot, then the user's ID — and the code trusts the ID without
> ever verifying the hash. Any user can set that number to anything and become
> anyone. Four lines, and it looks like ordinary parsing.
>
> And down here — the docs reviewer didn't just flag missing docstrings. It found
> one that's *wrong*: it promises a signed token that expires in 24 hours. Nothing
> in that function signs anything or expires. A reviewer grepping for missing
> docstrings would never catch a docstring that lies."

#### 2:25 – 2:35 · Stop the timer

**On screen:** Timer, then the review's header line.

> "{{BOB_TIME}}. And it's formatted to paste straight into GitHub."

---

### 2:35 – 2:52 · Impact and close (17s)

**On screen:** Split — your manual notes beside `PR-42-review.md`.

> "I reviewed this same PR by hand first. {{MANUAL_MINUTES}} minutes,
> {{MANUAL_FOUND}} of the {{PLANTED}} real issues. Bob's four parallel agents:
> {{BOB_TIME}}, {{BOB_FOUND}}. Same reviewer, same PR — the difference is that
> four specialists read it instead of one tired generalist reading it four times."

**End card:** repo URL.

---

## Recording notes

**Do not narrate the waiting.** If the parallel run takes 90 seconds, cut it to
15 and put a "2× " or "cut" marker on screen. Judges know you compressed it; the
`run-metadata.json` timestamp is your proof of the real number. Padding dead air
is how a 3-minute video runs out of time before the findings.

**The Tasks panel shot is non-negotiable.** It is the single frame that proves
"parallel subagents" rather than "AI wrote some text." Hold it long enough that a
judge scrubbing the timeline lands on it.

**Say "IBM Bob" out loud at least three times** — at 0:20, 0:50, and 2:35. Bob
being a core visible component is an eligibility requirement, not a stylistic one.
Don't rely on the UI being recognizable in a compressed player.

**Read the spotlighted bug slowly.** The token bug is the emotional peak of the
video and it takes a beat to land. Everything else can be brisk.

**Record segments separately and cut them together.** One continuous take will
fail on the third attempt and you'll start rushing.

---

## If a subagent fails on camera

Keep it. Narrate it: *"the style reviewer errored — the orchestrator reports three
of four and says so rather than pretending."* Graceful degradation is a feature you
actually built (orchestrator Step 2), and demonstrating it beats a reshoot you may
not have Bobcoins for.
