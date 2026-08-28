# Cue card — keep this on your phone while recording

Record continuously. Don't stop if you fumble a line — just pause, say it again,
and cut the bad take out later. Aim for ~6 minutes raw; you'll trim to under 3:00.

---

**1. THE DIFF** — tab: `pr/PR-1.diff`, scroll slowly

> "This is a sixty-seven line pull request. To review it properly I have to check
> four different things — is it secure, does it follow our style guide, is it
> tested, is it documented. I check them one after another, in my head, and by the
> fourth one I'm skimming. That's twenty to forty minutes, and the last thing I
> check is the thing I miss."

---

**2. THE MODES** — Bob Settings → Modes

> "So I built four specialists in IBM Bob. Security, style, test coverage, docs.
> Each has one job and an explicit list of things that are not its job. And instead
> of running one after another, they run at the same time."

---

**3. THE STYLE GUIDE** — tab: `bob-config/style-guide.md`, 3 seconds

> "The style reviewer has no rules built into it. It reads this — our actual style
> guide — and has to cite the clause number on every finding."

---

**4. DISPATCH** — Bob panel, New task, mode `Agent`, paste and send

> "One prompt in Agent mode dispatches all four against this PR."

---

**5. THE PARALLEL RUN** — hold on the Tasks panel. THE IMPORTANT SHOT. Let it breathe.

> "Four subagents, four tasks, running in parallel — not queued. Each one reading
> the same diff from a completely different angle."

*(then stay quiet and let it run — you'll cut this down later)*

---

**6. THE JSON** — Explorer, `reviews/raw/` filling with four files

> "Each one writes structured JSON against a shared schema. Severity, file, line,
> evidence, and a fix — not prose. That's what makes the merge possible."

---

**7. THE FINDINGS** — tab: `reviews/PR-1-review.md`, scroll to finding #1, then to the docs finding

> "Here's the one I want to show you. This PR adds token authentication. The token
> is a hash, then a dot, then the user's ID — and the code trusts the ID without
> ever verifying the hash. Any user can set that number to anything and become
> anyone. Four lines, and it looks like ordinary parsing."
>
> "And the docs reviewer didn't just flag missing docstrings. It found one that's
> wrong — it promises a signed token that expires in twenty-four hours. Nothing in
> that function signs anything or expires. A reviewer grepping for missing
> docstrings would never catch a docstring that lies."

---

**8. CLOSE** — `reviews/run-metadata.json` beside the review

> "Four specialist reviews, dispatched together, done in ninety-eight seconds. Full
> consolidated review in six minutes. Thirty-seven findings merged to seventeen —
> four critical, each one a merge blocker. And notice the timing field reads null:
> IBM Bob has no clock, so it won't report a number it can't measure. Everything
> you just saw was measured outside the agent."

---

## Do not say

- Any claim that *you* timed a manual review. You didn't.
- Any number not on this card.

## Say "IBM Bob" out loud at beats 2, 4, and 8.
