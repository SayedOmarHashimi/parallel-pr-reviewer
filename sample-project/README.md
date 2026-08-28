# devnotes — sample project under review

A small Flask note-taking API. **This is a fixture, not a product.**

It was written intentionally imperfect so the IBM Bob parallel review subagents
have something real to find: security flaws, style-guide violations, untested
code paths, and missing documentation.

## ⚠️ About the credential-looking strings

`config.py` contains strings that look like API keys and a database password.
They are **fake, hand-typed placeholders** created for this hackathon demo. They
authenticate against nothing and were never valid. They exist so the
`security-reviewer` subagent has a hardcoded-secret finding to report.

No real credential — IBM Cloud or otherwise — appears anywhere in this repo.

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Test

```bash
pytest tests/ -q
```
