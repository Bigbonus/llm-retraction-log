# G1 and G2 results (Claude), answering SUB70_G1_G3_EVIDENCE_DESIGN_REVIEW_V1

Frozen rows only (ts <= 2026-08-22T09:00:00), the seven Appendix C waves, no model, CPU only.
Scripts and outputs in this directory. Manuscript untouched.

## G1: schema-free estimator, `between_repeat_phi.py`

Standard library only. Input is a CSV with columns cell, repeat, correct. Self-test is built in.

- Self-test (`--selftest`): known-good binomial repeats (60 cells x 4 repeats x 12 rows) read phi 0.892,
  permutation p 0.89; known-bad Beta-binomial with phi_true 2.0 read phi 1.809, p 0.001. PASS.
- Parity (`g1_export_design_cells.py`): the paper's 166 design cells exported to the CSV (31,938 rows)
  give phi 1.076, df 1,424, 166 cells, permutation p 0.164 — equal to Appendix C pooled
  (G1_REPRODUCTION_V1.json, match true). The schema-free script is the same estimator.
- Limit: MIN_N = 4 rows per cell and at least two repeats, as in the paper. Cells at ceiling or
  floor contribute nothing; a log with few repeats gives few df and a wide permutation null.

## G2: flag rate of the readable rule on same-condition repeats, `g2_readable_false_alarm.py`

Rule fixed before analysis: readable(n1, n2) = 2 sqrt(1.08 (0.25/n1 + 0.25/n2)). Repeats with >= 4
rows, cells with pooled rate strictly inside (0, 1). Waves 2 and 3 have no repeat with >= 4 rows and
drop out, so this is 5 waves, 120 cells.

| statistic | pairs | rate |
|---|---|---|
| observed, all within-cell pairs (share observations) | 1,565 | 0.0058 |
| observed, one disjoint pair per cell step (independent) | 293 | 0.0102 |
| permuted null (outcomes shuffled across the two repeats, 200x) | 313,000 | 0.0100 |
| known-bad: one repeat moved 0.5 in rate (clipped) | 1,565 | 0.2486 |

By smaller repeat size: n 4–7 (1,082 pairs) observed 0.008, null 0.012, known-bad hit 0.111;
n 8–15 (483 pairs) observed 0.000, null 0.006, known-bad hit 0.557. No pair had n >= 16.
Cells with at least one flagged pair: 5 of 120.

What this supports: on real repeats the rule fires at the permuted-null rate (about 1%), below the
4.5% a two-SE rule at p = 0.5 would give; the p = 0.5 bound is conservative away from 0.5, which is
why. So the rule does not manufacture readable differences from noise on these logs.

What it also shows, and the paper should say: at the repeat sizes this programme actually has
(mostly 4–7 rows), the rule misses a true 0.5 shift 89% of the time, and 44% at 8–15 rows. That is
the rule working as designed (it refuses to read small-n differences) and it is the cost of it: the
floor is coarse, not sharp. It is a miss rate, not a false-alarm rate, and both belong in App C.

Limits (explicit, per Codex): phi = 1.08 was estimated on these same repeats, so this is not an
out-of-sample calibration of phi, only of the rule given phi; pairs inside a cell share observations
(the disjoint figure is the independent one); repeat counts are small; two of seven waves give no
usable pair; the known-bad shift is clipped at 0 and 1, so at extreme rates the injected difference
is smaller than 0.5 and the hit rate is a lower bound.

## Proposed App C text (two sentences, not applied)

"A schema-free implementation of the estimator with a built-in self-test is released with the audit
files; on the 166 design cells it reproduces phi = 1.08 exactly. Applied to 1,565 pairs of repeats of
the same design cell, the readable rule fires on 0.6% (permuted null 1.0%); with one repeat shifted
by 0.5 it fires on 25%, and on only 11% where repeats have 4–7 rows, so at this programme's repeat
sizes the floor is coarse by design."
