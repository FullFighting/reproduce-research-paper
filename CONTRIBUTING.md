# Contributing

Contributions are welcome for new extractors, comparison policies, isolation controls, documentation, and public low-cost paper cases.

Before a pull request:

```powershell
python -m compileall -q skills/reproduce-research-paper/scripts
python -m unittest discover -s tests -v
```

For behavior changes:

1. describe the affected source-to-report path;
2. add a regression test that fails without the change;
3. state whether plan validation, repository binding, observation extraction, status, write/network/resource policy, secrets, or privacy changes;
4. preserve old failed evidence rather than editing it into a passing result;
5. cite official paper, code, data, and license sources for benchmark cases;
6. keep runtime code compatible with Python 3.10+ and the standard library, with optional imports only for optional formats.

Never commit credentials, private datasets, paywalled text, proprietary model weights, or third-party data without redistribution permission.
