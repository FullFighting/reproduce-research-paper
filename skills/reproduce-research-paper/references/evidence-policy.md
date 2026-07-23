# Evidence policy

Use this policy to classify a claimed result.

## Claim record

Every claim needs an identifier, paper location, metric or visual target, reported value, tolerance, protocol note, and the command(s) expected to produce its evidence. Keep each target narrow: a table cell, one aggregate metric, a plotted series, or an ablation row.

## Evidence levels

- `declared`: appears in the paper but was not tested.
- `artifact_present`: code, data, or configuration exists but was not executed.
- `executed`: a recorded command produced an output, but the output has not been compared with the paper.
- `compared`: output was compared under a predeclared protocol and tolerance.
- `verified`: every required target for the claim was executed and compared within tolerance.

Do not upgrade an evidence level because a README asserts that a result is reproducible.

## Status rules

Use `VERIFIED` only for an executed and comparable target within its stated tolerance. Use `CONTRADICTED` when an executed comparable target is outside tolerance. Use `BLOCKED` when required inputs, access, or environment prerequisites are absent. Use `PARTIAL` for mixed claim outcomes. Use `NOT_RUN` when no relevant command was executed.

Never treat a code crash as evidence that the paper is false. Never treat a successful process exit as evidence that a claim is true.
