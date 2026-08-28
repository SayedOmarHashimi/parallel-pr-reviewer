# Video demo script — Parallel PR Reviewer

**Hard limit: 3:00.** Target 2:57. If a take runs over, cut in this order:
the style-guide cutaway at 1:05 (−3s), then the dispatch hold at 0:35 (−5s).
Requirement: 90+ seconds of the solution working live, narrated, with Bob visibly
doing the work.

---

## Measured numbers — all final, nothing to fill

| | Value |
|---|---|
| Four parallel reviews | **98 s** (longest subagent 1m38s, all from one dispatch) |
| End to end, prompt to finished review | **6 min 12 s** |
| Findings | **37 raw → 17 merged** |
| Severity | 4 critical · 8 high · 4 medium · 1 low |
| Verdict | Request changes |

**No human baseline was measured, so do not claim one.** Do not say "a manual review
takes 25 minutes" on camera — you did not time one. Say what the PR contains and
what Bob found. The 20–40 minute figure in the opening is a statement about code
review generally, not a measurement of you; keep it phrased that way.

**Bob has no clock.** It reports `null` for timing, and the review itself reads
"Reviewed by four parallel passes in N/A (timing not available)". That is a feature
worth one sentence on camera — an agent declining to state something it cannot
measure — not something to hide.

## Pre-record checklist

- [ ] Bob IDE at **160%+ zoom**. Judges watch this in a small embedded player.
- [ ] Editor theme: high contrast. Default dark themes lose thin syntax colors on re-encode.
- [ ] Close every unrelated panel, tab, notification, and Slack.
- [ ] `reviews/raw/` **emptied** — the files must appear on camera, not sit there pre-made.
- [ ] `pr/PR-1.diff`, `orchestrator.md`, and the Modes panel each pre-opened in a tab so you never hunt for a file mid-take.
- [ ] Screen recording at 1080p minimum.
- [ ] **Scrub for credentials:** no IBM Cloud account id, no API key, no email in any visible panel, title bar, or notification.
- [ ] Do a silent dry run of the click path once. The demo must not be the first time you click it.

---

## Screen layout

Record **one fixed region** for the entire video: Bob IDE filling the top ~85% of
the frame, a short terminal strip pinned along the bottom. Never app-switch and
never resize mid-take — a frame that changes shape between cuts reads as sloppy,
and the upload re-encode makes it worse.

```
┌──────────────────────────────────────────────────────────┐
│  Bob IDE                                                 │
│  ┌──────────┬───────────────────────┬─────────────────┐  │
│  │ Explorer │  Editor               │  Bob panel      │  │
│  │          │                       │  (Modes /       │  │
│  │ reviews/ │  whatever the current │   Agent mode /  │  │
│  │   raw/   │  beat needs open      │   Tasks)        │  │
│  └──────────┴───────────────────────┴─────────────────┘  │
├──────────────────────────────────────────────────────────┤
│  terminal — ELAPSED  01:24                               │
└──────────────────────────────────────────────────────────┘
```

Three regions, three jobs. **Explorer** left, pinned to `reviews/` so the JSON
files visibly appear during the run. **Editor** centre, the only thing you change
between beats. **Bob panel** right, switching Modes → Agent mode → Tasks. The
terminal strip only ever holds the stopwatch.

### The stopwatch

Run this in the bottom strip before you start. It is what makes "under three
minutes" a thing the viewer watches rather than a thing you assert:

```bash
s=$(date +%s); while :; do e=$(( $(date +%s)-s )); printf "\r  ELAPSED  %02d:%02d" $((e/60)) $((e%60)); sleep 1; done
```

Terminal font at 24pt or larger, and `Ctrl-C` to stop it. Start it at the moment
you submit the orchestrator prompt, not before.

### What is in the editor, beat by beat

| Beat | Editor shows | Bob panel shows |
|---|---|---|
| 0:00 problem | `pr/PR-1.diff`, scrolling | anything, not the focus |
| 0:20 the idea | — | **Modes**, all four visible |
| 0:35 dispatch | `bob-config/orchestrator.md` | **Agent mode**, prompt pasted |
| 0:50 parallel run | — | **Tasks**, four running · *hero shot* |
| 1:05 cutaway | `bob-config/style-guide.md` (3s) | Tasks, still running behind |
| 1:15 output | `reviews/raw/security.json` | Tasks, completing |
| 1:35 synthesis | `reviews/PR-1-review.md` being written | Agent mode |
| 1:55 findings | `reviews/PR-1-review.md`, **rendered preview** | — |
| 2:35 impact | `metrics/manual-baseline.md` split with the review | — |

Read the final review as **rendered markdown**, not raw source. The consolidated
review is a designed artifact — severity headings, per-finding reviewer tags — and
raw `##` and backticks throw that away in the one shot where it matters.

### Before you hit record

- **Do Not Disturb on.** One Slack toast over the Tasks panel costs you a take.
- **Hide the Dock** (`⌥⌘D`) and clear the menu bar of anything identifying.
- Editor at **160%+**, terminal at **24pt+**.
- Empty `reviews/raw/` — the files must appear on camera, not sit there pre-made.
- Pre-open every file listed above in its own tab, in beat order, left to right.
  You should never search for a file on camera.

## Script

### 0:00 – 0:20 · The problem (20s)

**On screen:** `pr/PR-1.diff` open, scrolling slowly.

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

**On screen:** Agent mode merging; `reviews/PR-1-review.md` being written.

> "Then Agent mode merges all four. It deduplicates — two reviewers flagged the
> same swallowed exception — ranks by severity, and every finding keeps the name
> of the subagent that found it."

#### 1:55 – 2:25 · The findings — *land the specific one*

**On screen:** `PR-1-review.md`, scroll to the top finding, then to the docs finding.

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

> "Six minutes twelve, start to finish. And it's formatted to paste straight into GitHub."

---

### 2:35 – 2:57 · Impact and close (22s)

**On screen:** `reviews/run-metadata.json` beside `PR-1-review.md`.

> "Four specialist reviews, dispatched together, done in ninety-eight seconds.
> Full consolidated review in six minutes. Thirty-seven findings merged to
> seventeen — four critical, each one a merge blocker. And notice the timing field
> reads null: IBM Bob has no clock, so it won't report a number it can't measure.
> Everything you just saw was measured outside the agent."

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
