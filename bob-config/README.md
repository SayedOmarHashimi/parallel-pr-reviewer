# Bob configuration

Four subagent role definitions, the style guide one of them enforces, and the
JSON contract all four emit.

```
subagents/01-security-reviewer.md      → Bob custom mode `security-reviewer`
subagents/02-style-reviewer.md         → Bob custom mode `style-reviewer`
subagents/03-test-coverage-reviewer.md → Bob custom mode `test-coverage-reviewer`
subagents/04-docs-reviewer.md          → Bob custom mode `docs-reviewer`
style-guide.md                         → input document for the style reviewer
finding-schema.json                    → output contract for all four
```

## Registering the subagents in Bob IDE

For each file in `subagents/`:

1. Bob IDE → **Modes** → **New custom mode**.
2. Name it exactly as the `Bob custom mode name` line specifies. The orchestrator
   prompt calls them by these names.
3. Paste everything below the `---` as the mode instructions.
4. Save.

Capture a screenshot of the four modes registered → `bob_sessions/01-subagent-setup.png`.

## Why four narrow agents instead of one broad one

Each definition contains an explicit **"Not your job"** section. That is the whole
design. A single reviewer asked to check four concerns at once spreads attention
thin and reports whichever concern it noticed first. Four agents with hard mandates
each read the same diff four times, from four angles, and none of them get to skip
the boring pass because they already found something interesting.

The mandates are deliberately non-overlapping, with one intentional exception:
bare `except:` is both a style guide violation (rules 4.1/4.2) and a security
smell. Both reviewers report it; the orchestrator dedupes. Better a duplicate than
a gap where each agent assumed the other had it.

## Document understanding

`style-reviewer` does not carry a hardcoded list of style rules. It reads
`style-guide.md` — a real 50-line policy document with numbered clauses — and must
cite the clause number it is enforcing on every finding. Swap in a different
team's style guide and the agent's behavior changes with no prompt edits. This is
the "document understanding" leg of the submission: an agent whose rules live in a
document a human maintains, not in the agent.

## Running

The four modes run **concurrently** against the same diff, each writing to
`reviews/raw/`. Agent mode then merges the four JSON files into one review.

The orchestration prompt lives in `bob-config/orchestrator.md`.

## Bobcoin budget

40 coins total, no refills. A full four-subagent parallel run plus synthesis is
your expensive operation — budget for **at most 3 or 4 complete runs**, so:

- Dry-run a single subagent on one file first to confirm the JSON shape is right.
  Fixing the contract after four parallel agents have already burned coins is the
  expensive mistake.
- Get your screenshots on the first *good* run. Do not plan on a re-run for
  better-looking screenshots.
- `.bobignore` excludes `node_modules`, `.git`, `bob_sessions/`, and the scoring
  answer key — that is context you would otherwise pay for on every run.
