# Written statement 2 — How IBM Bob was used

**No stated word limit**, but specificity is the scored quality, not length.
Only the text between the markers is submitted.

> ⚠️ **Verify every UI label against your actual build (v2.0.3) before submitting.**
> I have written these as *Modes*, *Agent mode*, and *Tasks panel*. If your Bob
> names any of them differently, correct it here and in the video narration. A
> judge who uses Bob daily will notice a wrong panel name, and it undercuts the
> claim that Bob was central to the build.

<<<SUBMIT

## How IBM Bob was used

IBM Bob IDE v2.0.3 is not an assistant in this project — it is the runtime. Every
review finding in this submission was produced by Bob. The repository contains the
fixture under review, the agent definitions, and the evidence; it contains no
review logic of its own, because the orchestration *is* Bob.

### 1. Custom Modes — four specialist subagents

I created four custom modes in Bob's **Modes** panel, one per review concern:
`security-reviewer`, `style-reviewer`, `test-coverage-reviewer`, and
`docs-reviewer`. Each mode's instructions are checked into the repository at
`bob-config/subagents/`.

Each definition contains a mandate, a severity rubric, anti-fabrication rules, and
— the design decision the whole system rests on — an explicit **"Not your job"**
section. The security reviewer is instructed to ignore naming and formatting even
when glaring; the style reviewer is instructed to ignore vulnerabilities. Narrow
mandates are what stop four agents from producing four copies of the same shallow
review.

### 2. Agent mode — parallel dispatch and synthesis

The orchestration prompt at `bob-config/orchestrator.md` runs in Bob's **Agent
mode**. It performs five steps:

1. Dispatches all four subagents **concurrently** against the same diff — not
   queued, not chained. Bob's parallel task execution is the mechanism that turns
   four sequential passes into one wall-clock pass.
2. Collects and validates four JSON files, reporting any subagent that failed
   rather than silently presenting a three-agent review as four.
3. Merges: deduplicates findings reported by multiple reviewers, keeps the higher
   severity rather than averaging, ranks by severity then confidence, and preserves
   the originating subagent on every finding.
4. Renders a consolidated review formatted to paste into GitHub.
5. Writes `reviews/run-metadata.json` with per-subagent timings — the measurements
   in this submission are Bob's own recorded output, not stopwatch recollections.

Agent mode is explicitly instructed that it does not review. It has no findings of
its own and may not attribute anything to a subagent that the subagent did not
report.

### 3. Document understanding — rules that live in a document

`style-reviewer` has no style rules in its prompt. It reads
`bob-config/style-guide.md`, a numbered 50-clause engineering policy document, and
must cite the clause number on every finding — a finding with no clause number is
defined as invalid and discarded. Bob interprets the document at review time.
Replacing that file with another team's guide changes the agent's behavior with no
prompt edits, which is what makes this adoptable rather than a demo.

### 4. Structured output contract

All four subagents emit findings against a single schema,
`bob-config/finding-schema.json`: severity, confidence, file, line, symbol, verbatim
evidence, and a concrete fix. Structured output is what makes the merge
deterministic; merging four prose reviews would require the orchestrator to
re-interpret them, and re-interpretation is where invented findings enter.

### 5. Context control with `.bobignore`

`.bobignore` excludes credentials, dependency directories, Bob's own session
exports, and the scoring key that catalogues the fixture's planted defects. This
serves three purposes: it keeps secrets out of Bob's context and out of published
screenshots, it prevents the reviewing agents from reading the answers, and it
holds down token cost on every run.

### 6. Two honest limitations found while building this

**Bob has no wall clock.** Early runs emitted confident-looking timestamps that were
over a year off. The orchestrator prompt now instructs it to write `null` for any
field it cannot observe, and the shipped review reads "Reviewed by four parallel
passes in N/A (timing not available)". All timings in this submission are measured
externally, from artifact modification times and a screen recording, with the method
recorded in `reviews/run-metadata.json`.

**Subagents did not inherit their mode's write permission.** In the submission run,
two of the four reviewers executed without file-write rights and returned their
findings as chat output; the orchestrator transcribed those into
`reviews/raw/security.json` and `reviews/raw/style.json`. All four still ran
concurrently from a single dispatch. This is disclosed in the run metadata and in the
review's Reviewer status table rather than smoothed over, because a provenance claim
that is not exactly true is worth less than no claim.

### 7. Evidence

`bob_sessions/` contains task session summaries exported from Bob's **Tasks**
panel, including the four subagents running concurrently and the Agent mode
synthesis pass. `reviews/raw/` retains each subagent's unmerged JSON, so any line
in the final review can be traced back to the agent that produced it.

SUBMIT>>>
