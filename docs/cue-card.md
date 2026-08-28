# Cue card — final. Keep on your phone while recording.

**No live Bob run.** Everything is already on disk. You click through and narrate.
Beat 5 is a clip you splice in afterward.

Record continuously. If you fumble, pause, say the line again, keep going — you'll
cut the bad takes out. Aim for ~4 minutes raw, trim to under 3:00.

---

## Before you hit record

**Open these four tabs in Bob, left to right (double-click each so they pin):**

1. `pr/PR-1.diff`
2. `bob-config/style-guide.md`
3. `reviews/PR-1-review.md`
4. `reviews/run-metadata.json`

**Plus:** Bob Settings open on the **Modes** page (not General — that shows your email).

**In the Explorer:** expand `reviews/` and `reviews/raw/` so the four JSON files are visible.

**Screen:** Do Not Disturb on · Dock hidden (`Opt+Cmd+D`) · editor zoom ~160%

**Record:** `Cmd+Shift+5` → Options → Save to `hackathon-recordings` → Record Selected
Portion → box around the Bob window → Record. Wait 3 silent seconds, then start.

---

## 1. THE DIFF
**Show:** tab `pr/PR-1.diff` — scroll slowly and steadily the whole time you talk.

> "This is a sixty-seven line pull request. Reviewing it properly means checking four
> different things — is it secure, does it follow the style guide, is it tested, is it
> documented. One reviewer does them one after another, in one head, under deadline
> pressure. Code review like this runs twenty to forty minutes, and the concern you
> check last is the one you skim."

---

## 2. THE MODES
**Show:** Bob Settings → Modes. Four Workspace reviewers under the three built-ins.

> "So I built four specialists in **IBM Bob**. Security, style, test coverage, docs.
> Each has one job and an explicit list of things that are not its job. And instead of
> running one after another, they run at the same time."

---

## 3. THE STYLE GUIDE
**Show:** tab `bob-config/style-guide.md` — scroll past the numbered rules. ~5 seconds.

> "The style reviewer has no rules built into it. It reads this — the team's actual
> style guide — and it has to cite the clause number on every finding. Swap in a
> different team's guide and the agent changes behaviour with no prompt edits."

---

## 4. DISPATCH
**Show:** Bob panel with the orchestrator prompt visible in the task box.

> "One prompt in **IBM Bob's** Agent mode dispatches all four against this PR."

---

## 5. THE PARALLEL RUN  ← spliced clip, narrate over it
**Clip:** `hackathon-recordings/beat5-parallel-run-clip.mov` (22 s)

> "Four subagents, four tasks, running in parallel — not queued. Each one reading the
> same diff from a completely different angle."

*(then go quiet and let the clip play out)*

---

## 6. THE JSON
**Show:** Explorer `reviews/raw/` — click `security.json` open briefly.

> "Each one writes structured JSON against a shared schema. Severity, file, line,
> evidence, and a fix — not prose. That's what makes the merge deterministic."

---

## 7. THE FINDINGS
**Show:** tab `reviews/PR-1-review.md`. Start at the top, scroll to finding #1, then
down to the docs finding. Read slowly — this is the peak.

> "Here's the one I want to show you. This PR adds token authentication. The token is
> a hash, then a dot, then the user's ID — and the code trusts the ID without ever
> verifying the hash. Any user can set that number to anything and become anyone. Four
> lines, and it looks like ordinary parsing."
>
> "And the docs reviewer didn't just flag missing docstrings. It found one that's
> wrong — it promises a signed token that expires in twenty-four hours. Nothing in that
> function signs anything or expires. A reviewer grepping for missing docstrings would
> never catch a docstring that lies."
>
> "And it's formatted to paste straight into GitHub."

---

## 8. CLOSE
**Show:** tab `reviews/run-metadata.json` — point at the `started_at: null` line.

> "Four specialist reviews, dispatched together, done in ninety-eight seconds. Full
> consolidated review in six minutes. Thirty-seven findings merged down to seventeen —
> four of them critical, each one independently a merge blocker. And notice the timing
> field reads null: **IBM Bob** has no clock, so it won't report a number it can't
> measure. Everything you just saw was measured outside the agent."

**End card:** github.com/SayedOmarHashimi/parallel-pr-reviewer

---

## Rules

- Never claim *you* timed a manual review. The twenty-to-forty is about code review
  generally, not about you.
- Say no number that isn't on this card.
- "IBM Bob" out loud at beats 2, 4, and 8.
- Scroll slower than feels natural. Fast scrolling turns to mush when compressed.
