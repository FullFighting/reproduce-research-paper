# Repository guidance

Maintain an evidence-first Codex Skill for computational research reproduction.

## Constraints

- Keep `skills/reproduce-research-paper/scripts/` compatible with Python 3.10+ and the standard library.
- Do not equate a successful process exit with a verified research claim.
- Require paper location, declared metric, expected value, tolerance, and observed output for a verified claim.
- Keep command execution behind an explicit `--execute` flag.
- Never add access-control bypasses, credential collection, automatic package installation, hidden network requests, or fabricated result recovery.
- Keep original research repositories immutable; direct generated logs and reports to a separate output directory.

## Validation

Run before proposing changes:

```bash
python -m compileall -q skills/reproduce-research-paper/scripts
python -m unittest discover -s tests -v
```

## Pull requests

Explain the claimed behavior being changed, include a regression test, and state the effect on evidence classification, command execution, privacy, and reproducibility reports.
