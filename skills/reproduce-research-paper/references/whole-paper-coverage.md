# Whole-paper coverage

Whole-paper reproduction does not mean rerunning every experiment blindly. It
means that after reading the entire paper, every experiment, reported value,
and conclusive statement receives an explicit, honest status — reproduced,
manually reviewed, blocked, or deliberately not attempted — and that every
expected value used for reproduction is quoted verbatim from the paper.

## The claims map

Author a claims map (`paper-claims-map.json`, schema v1) after reading the
whole paper and before authoring reproduction plans:

- `paper`: at least a non-empty `title`.
- `coverage.read_completely`: must be `true`. A partial reading cannot ground
  a whole-paper map.
- `coverage.sections`: every section that was read.
- `coverage.excluded_content`: content deliberately left out, each entry with
  a `location` and a `reason` (for example supplementary videos).
- `claims`: one entry per experiment, reported value, figure, and conclusive
  statement in the paper.

Each claim carries:

- `claim_type`: `quantitative`, `conclusion`, `qualitative`, `visual`, or
  `theoretical`.
- `paper_location`: exact section, table, figure, or page.
- `paper_quote`: the verbatim sentence(s) from the paper making the claim.
- `paper_values`: the reported values, copied verbatim; every entry must be a
  substring of `paper_quote`. Required for quantitative claims.
- `disposition`: `reproduce`, `manual_review`, `not_reproducible`, or
  `not_attempted`. Every non-`reproduce` disposition needs a `reason`.
- `plan_claim_ids`: for reproduced quantitative claims, the reproduction-plan
  claims that verify this paper claim.
- `supported_by`: for conclusion claims, the non-conclusion claims whose
  outcomes decide the conclusion's status.

## Paper-grounded expected values

`validate_paper_claims_map.py --map <map> --plan <plan>` enforces:

- every `paper_values` entry appears verbatim inside `paper_quote`;
- every plan claim is referenced by the map — a plan claim with no paper
  grounding is an error, because expected values must come from the paper;
- every numeric expected value in a referenced plan claim matches a number
  quoted in `paper_values` (percent forms such as `91.5%` also ground `0.915`);
- string, categorical, and table-label expected values appear in the quote;
- an `artifact_hash` expected value is valid only when the paper itself
  publishes the digest.

Never invent, average, round, or "correct" a paper value to make grounding
pass. If the paper does not state a value, the claim cannot use disposition
`reproduce`.

## Conclusive statements

A conclusion (`claim_type: "conclusion"`) is never verified by prose
agreement. It inherits its status from the outcomes of the claims listed in
`supported_by`:

- all supporting claims `CLAIM_REPRODUCED_WITHIN_TOLERANCE` → the conclusion's
  computational support is reproduced;
- mixed outcomes → `PARTIALLY_REPRODUCED`;
- unresolved or blocked support propagates honestly.

Even a fully supported conclusion remains a statement about the declared
computations, not about scientific truth, causality, or generalization.

## Dispositions map to statuses

| Disposition | Resolved status |
|---|---|
| `reproduce` | Aggregated from linked plan claims or supporting claims |
| `manual_review` | `MANUAL_REVIEW_REQUIRED` |
| `not_reproducible` | `BLOCKED` |
| `not_attempted` | `NOT_ATTEMPTED` |

## Coverage report

`build_coverage_report.py --map <map> --bundle <bundle> [--bundle ...]
--output <dir>`:

1. re-validates the claims map;
2. verifies every supplied evidence bundle end to end (provenance,
   bindings, recomputed comparisons) and refuses unverifiable bundles;
3. re-checks paper grounding against each bundle's embedded plan;
4. resolves one status per mapped claim, then conclusions from their support;
5. writes `coverage.json` and `coverage-report.md` with per-claim statuses,
   verbatim quotes, bundle hashes, and interpretation limits.

The overall status aggregates all mapped claims. A paper containing any
visual-only or blocked claim can never exceed `PARTIALLY_REPRODUCED`; that is
correct behavior, not a defect. Do not shrink the map to inflate coverage —
removing a claim from the map is falsifying coverage, not improving it.
