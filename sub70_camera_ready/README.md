# Camera-ready audit files for "Answers Without the Model" (NeurIPS 2026 Workshop AI-Native Academia, Submission 70)

Everything the camera-ready version cites as released. Nothing here runs a model; all scripts read
frozen evaluation logs (rows with `ts <= 2026-08-22T09:00:00+09:00`) and recompute the paper's figures.
Paths inside the scripts are the author's local paths and are left as they were run; each result file
records the input file hashes it was computed from.

## paper_scripts/
- `mythos_freeze_corpus_v1.py`, `MYTHOS_PAPER_CORPUS_FREEZE_V1.json` — the corpus freeze rule and the freeze table (Appendix A: 20 waves, 79,021 rows, 77,293 scored, per-file row counts, minimum-rows-per-model rule).
- `mythos_paper_verify_v1.py` — the 42-check verification script (Appendix E).
- `mythos_noise_floor_v1.py` — the submitted over-dispersion estimator. It is kept as the record of the defect described in Sec. 5: for binary data it returns n/(n-1).
- `mythos_cross_wave_v1.py` — the temperature meta-analysis (Appendix D).
- `mythos_claim_audit_v1.py` — the corpus-wide cell-pair enumeration (Sec. 3, 46,279 pairs).

## audit_v1/
The independent audit behind the camera-ready corrections (Sec. 3 estimator, Sec. 2.1 attribution, Appendix D truncation).
`EVIDENCE_MEMO_V2.md` is the audit memo; `a1_phi_identifiability.py` and `A_PHI_RESULT_V1.json` hold the identity
check, injection and simulation results; `a1b_*`/`a1c_*` the permutation test and power; `b1`–`b4` the temperature and
truncation analysis; `c1`–`c2` the leak attribution. Each script re-implements the paper's computation, reproduces the
submitted figure, and checks that it fails on a known-bad input before reporting anything new.

## audit_extra/
`d1_cell_pairs.py` / `D1_CELL_PAIRS_V1.json` — recomputation of the corpus-wide readable-pair figures at phi = 1.08 and phi = 1.
`d2_floor_table.py` / `D2_FLOOR_TABLE_V1.json` — the minimum-readable-difference table and calibration thresholds.

## audit_extra_v3/
`between_repeat_phi.py` is a schema-free, standard-library implementation of the between-repeat estimator with a built-in self-test (`--selftest`); give it a CSV with columns cell, repeat, correct. `g1_export_design_cells.py` shows it reproduces Appendix C exactly on the paper cells. `g2_readable_false_alarm.py` / `G2_READABLE_FALSE_ALARM_V1.json` measure the readable rule on same-condition repeat pairs: observed flag rate, permuted null, and hit rate on an injected 0.5 shift, by repeat size. `G1_G2_RESULTS_V1.md` summarises both with their limits.
