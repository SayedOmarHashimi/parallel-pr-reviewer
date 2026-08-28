# Paste-ready mode content

One pair of files per subagent. Create the mode in Bob → Settings → Modes → `+`,
then copy each file into the matching box. Nothing needs editing.

| Box in Bob's form | What to put in it |
|---|---|
| **Slug** | the slug below |
| **Name** | the same string as the slug — the orchestrator calls modes by this name |
| **Description** | the description below |
| **Scope** | `Workspace` if offered, else `Global` |
| **Role definition** | paste `<slug>.ROLE.txt` |
| **When to use** | the description below (same text is fine) |
| **Mode-specific Custom Instructions** | paste `<slug>.INSTRUCTIONS.txt` |

## Available Tools — set these identically for all four

| Tool | Setting | Why |
|---|---|---|
| Read | **ON** | must read the diff and the source |
| Edit | **ON** | must write its JSON into `reviews/raw/` |
| Execute | OFF | nothing to run; the diff is already a file |
| MCP | OFF | no external servers involved |
| Skill | OFF | not used |
| Todo | OFF | not used |
| Subtask | OFF | reviewers do not decompose work |
| Subagent | **OFF** | reviewers must not spawn more agents — only the orchestrator does |
| Mode | OFF | a reviewer must not switch itself out of its own mandate |

Least privilege is deliberate: each reviewer can read the code and write one file,
and nothing else. It is also a talking point — the security reviewer cannot execute
anything it is reading about.

## The four modes

### `security-reviewer`

**Description / When to use:** Finds exploitable security defects in a code diff and reports them as structured JSON.

- Role definition → `security-reviewer.ROLE.txt`
- Custom Instructions → `security-reviewer.INSTRUCTIONS.txt`

### `style-reviewer`

**Description / When to use:** Checks a diff against the project's written style guide and reports violations as structured JSON.

- Role definition → `style-reviewer.ROLE.txt`
- Custom Instructions → `style-reviewer.INSTRUCTIONS.txt`

### `test-coverage-reviewer`

**Description / When to use:** Finds changed code paths with no corresponding test and reports the gaps as structured JSON.

- Role definition → `test-coverage-reviewer.ROLE.txt`
- Custom Instructions → `test-coverage-reviewer.INSTRUCTIONS.txt`

### `docs-reviewer`

**Description / When to use:** Finds missing and inaccurate documentation on changed code, reported as structured JSON.

- Role definition → `docs-reviewer.ROLE.txt`
- Custom Instructions → `docs-reviewer.INSTRUCTIONS.txt`
