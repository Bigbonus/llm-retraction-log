# Correction note V2: reporting corrections from SUB70_G1_G2_V2_WORDING_REVIEW_V1

Applies to G1_G2_RESULTS_V2.md and the V2 scripts. V2 files are kept; this note and the V3
estimator/test files are additions.

| V2 said or did | correction | where fixed |
|---|---|---|
| "preregistered here before running" (g2 v2 docstring, RESULTS_V2 table C) | code constants are not a timestamped pre-run record. Read as "simulation settings fixed in code". No pre-run record exists for the three (p1, p2) pairs. | this note; V4 App C text says "simulated power", not preregistered |
| test label "v1 silently dropped: blank cell" | V1 accepts a blank id as a group; it does not drop the row. Dropping applies only to invalid `correct` values. | test_between_repeat_phi_v3.py labels the two behaviours separately |
| "refuses malformed input" (V2) | tested cases only. V2 did not reject a duplicated required header after normalisation or a row with a different field count. | between_repeat_phi_v3.py refuses both; 12 checks pass; phi on the paper cells unchanged (166, 1,424, 1.076) |
| "no figure is an independent-sample estimate: pairs share rows, items, cells, waves" (applied to C as well) | the Monte Carlo draws are new; only the pair sizes come from the observed pairs. The dependence caveat is scoped to the observed and shuffled rates (A) and to the empirical size selection. | this note; V4 App C text |
| "9 negative and accounting tests" | 9 checks, not nine distinct malformed-input cases (Codex) | this note |

Status: Codex has not rerun G2 end-to-end or verified the repository contents. Nothing here is a
final release PASS.
