# EVIDENCE_MEMO_V2 (Sub70 camera-ready audit)

Built 2026-09-29 18:50:48 JST (clock at build time) per codex DECISION SUB70_AUDIT_MEMO_V2_REBUILD_V1. This V2 is the review source. EVIDENCE_MEMO_V1.md is kept unchanged (sha256 829dec6f76cd...).

## Provenance of this version

- Sections below 'V1 as cited' are byte-identical to the first 14,329 bytes of EVIDENCE_MEMO_V1.md, whose sha256 (d3841d0bbc69...) is the one cited by ledger row SUB70_CAMERA_READY_AUDIT_RESULT_V1 (2026-09-29 14:09).
- After that row, the auditing agent appended 339 bytes to V1 in place (a correction), which changed V1's hash to 829dec6f76cd. That in-place append is superseded by the Correction section here.

## Correction

Section B of V1 said qwen3:4b had "only 72" rows that did not hit the length cap. 72 is the number of SCORED rows inside strata that contain both temperatures (B_W18_MH_CI_V1.json, qwen3:4b no-cap strata: 23 + 49). The row-level count is 90 of 1,864 (B_SEC23_CAP_V1.json: 1,864 total, cap-hit rate 95.2%). The camera-ready draft uses 90 of 1,864. No other number in V1 is changed by this correction.

Verbatim text of the in-place append (for the record):

```
## Correction (appended after the camera-ready draft)

Section B says "only 72 of its rows did not hit the cap". 72 is the number of scored rows in strata that have both temperatures (B_W18_MH_CI_V1.json, no_cap qwen3:4b: 23 + 49). The row-level count is 90 of 1,864 (B_SEC23_CAP_V1.json: 1864 - 1774). The camera-ready uses 90 of 1,864.
```

---

## V1 as cited

# Sub70 camera-ready: independent audit of the three reviewer objections (V1)

Request: ledger id SUB70_CAMERA_READY_INDEPENDENT_AUDIT_V1 (codex, 2026-09-29 13:49 JST).
Auditor: claude (subagent). Directory created 2026-09-29T13:53:48+0900 (clock read); memo written after 2026-09-29T14:07:14+0900 (clock read).
Scope kept: read-only on the paper, logs, queue, models and experiments. No GPU, no model calls, no network. Everything below was produced by the scripts in this directory (run with `python -B`) from the frozen rows (`ts` <= 2026-08-22T09:00:00, rows without `ts` dropped), exactly as the paper defines its corpus.

## Inputs (verified)

| item | path | sha256 prefix |
|---|---|---|
| paper | G:\chappy_ai_storage\handoff\judge2026_submit\paper.tex | faee8aef4007 (matches request; re-checked at end) |
| appendix | G:\chappy_ai_storage\handoff\judge2026_submit\appendix.tex | a7a3140731e9 (matches; re-checked at end) |
| text mirror | G:\chappy_ai_storage\handoff\scratchpad_mirror\sub70_text.txt | 4350d79cca41 — **stale**: its Sec. 2.2 says "three models (n=92–96)"; paper.tex lines 142-145 say two auditable models, n=56–60. Use paper.tex, not the mirror. |
| log dir | G:\visual_rebuild_v2\06_learning\mythos_presence_v1\ | (git: no uncommitted change to any file used) |
| W18 log | mythos_relation_wave18_v1.jsonl | 1cef1c67933a |
| W19 log | mythos_relation_hard_wave19_v1.jsonl | 6ed461b0eac9 |
| phi waves | battery_wave6 463c8bbfda88 / exploration_wave2 951aeb54b285 / exploration_wave3 117af3dda90f / lepsilon_decisive_wave9 7395220c216b / reading_derived_wave11 d594c36338be / technique_wave5 dc074c93912a / type_decomposition_wave10 f3d8a64b14b4 / replication_wave4 85d926a8ad3e | |
| paper's scripts | mythos_noise_floor_v1.py a5df9a420a1f; mythos_cross_wave_v1.py 91684b1493e1; mythos_paper_verify_v1.py 5e4e1a9d92dd; runners mythos_relation_wave18_v1.py d905175a9901, mythos_relation_hard_wave19_v1.py d7bfd4827b07; mythos_probe_core_v1.py 97ffe444e384 | |

Files are append-only logs that grew after the cutoff; row sets are reconstructed by `ts`, as the freeze rule says.

---

## A. Estimator identifiability (PX8b objection 1) — **reviewer right**

Scripts: a1_phi_identifiability.py (93ceeb4954a0) -> A_PHI_RESULT_V1.json (c2c5d8b7e770), stdout a1_stdout.txt; a1b_fine_permutation.py (bdc5bd066882) -> A_PHI_FINE_PERMUTATION_V1.json (94a92501aa47); a1c_fine_power.py (b6d2c9ef0142) -> A_PHI_FINE_POWER_V1.json (0fffa7557c6e).

Calibration: re-implementing mythos_noise_floor_v1.py reproduces Appendix C exactly (7/7 waves: cells, mean cell n, phi; median 1.01; replication wave 4 all-ceiling). Known-bad: removing the cutoff changes wave 9 to (14 cells, 1399.2) and the check reports the mismatch.

Findings:
1. **The paper's statistic is a constant of the cell size, not a measurement.** For binary outcomes the per-cell ratio s^2 / (p(1-p)) equals n/(n-1) identically. Across all 84 non-degenerate cells, max |cell statistic - n/(n-1)| = 2.1e-14. The wave phis in Appendix C are predicted from cell sizes alone (e.g. wave 2: 1.0389, wave 3: 1.0506, wave 9: 1.0009). The largest value the statistic can take for n >= 4 is 4/3.
2. **It cannot detect over-dispersion.** Replacing real outcomes by the most over-dispersed pattern possible (each repeat group all-0 or all-1) leaves it at 1.001–1.057. In simulation using each wave's real repeat-group sizes and cell p, with known between-repeat phi_true = 1, 1.25, 1.5, 2, 3, it returns the same value (e.g. wave 6: 1.011 at every phi_true, sd <= 0.0006); its flag rate at the paper's own 1.15 reading rule is 0.00 at every phi_true.
3. **The paper's "cells" are not identical conditions.** The cell key omits the runner-named design cell (`cell` label minus repeat suffix). One paper cell pools 1–8 design cells (waves 2, 3, 6, 11), 6 (wave 5), 8 (wave 10), 26 (wave 9).
4. **An identifiable estimator exists in the same logs** (between-repeat Pearson X^2 of repeat-group counts against the cell p). Calibrated: permuted-null mean 0.99–1.07 per wave, extreme injection 2.97–130. On paper cells it gives 0.12–0.89 (under-dispersion, as expected when heterogeneous conditions are pooled with the same set in every repeat). On design cells (166 cells, 7 waves): pooled phi 1.076, df 1424, permutation p = 0.168 (1000 perms; permutation-null mean 1.033); per wave 0.68–1.15, lowest p = 0.053 (wave 9, phi 1.131, 81 cells; 4 cells at p < 0.01 vs 0.81 expected by chance under chi-square). Power on this structure (null-calibrated threshold 1.099): 0.52 for phi = 1.10, 0.98 for 1.25, 1.00 for 1.5.

Supports: a narrower statement — "on design cells, between-repeat dispersion is not detectably above binomial (pooled 1.08, permutation p = 0.17); this design detects phi >= 1.25 with ~0.98 power and phi = 1.10 with ~0.5". Does NOT support: "phi = 1.01 across eight waves", "binomial to within 5%", "no detectable drift, seed instability or contamination" as derived in the paper; the Appendix C table as evidence. Note also: only 7 waves give an estimate (the text says eight). The readable() thresholds themselves are standard 2-SE bounds (phi ~ 1) and the calibration table (0.58, 0.71, 0.07) does not depend on the estimate — that part stands as a 2-SE rule.

## B. Temperature vs truncation, wave 18 (PX8b objection 2) — **reviewer right** (mechanism partly different)

Scripts: b1_temperature_truncation.py (14cafbc9b6ed) -> B_TEMP_TRUNC_RESULT_V1.json (7a1b5edd1c14); b2_w18_design_balance.py (db076c949fd2) -> B_W18_BALANCE_V1.json (ce6cae257d65); b3_w18_mh_ci.py (630fbbfee7f6) -> B_W18_MH_CI_V1.json (7eefe81d652c); b4_sec23_capcheck.py (6906b1795971) -> B_SEC23_CAP_V1.json (e39d82cc7dec).

Calibration: re-implementing mythos_cross_wave_v1.py reproduces W18 OR 0.69, 1/var 178.3, and pooled OR 0.957 [0.905, 1.011], k 16, I2 44%, tau2 0.0046. Known-bad: no cutoff gives W18 OR 1.216; counting non-events as failures gives 0.597 — both flagged as not reproducing. Sec. 2.3 also reproduces (1,772 rows, 0.46, 0.31, 0.21, others 0.89–0.94, non-answer <= 0.01 after rounding); no-cutoff gives 2,942 rows (fails).

Field used: `done_reason == "length"` (num_predict = 160). The harness labels TRUNCATED_NO_VISIBLE_OUTPUT only when the cap is hit AND visible text is empty (mythos_probe_core_v1.py line 88); cap-hit rows with visible text are scored.

| W18 model | cap-hit T=0 | cap-hit T=0.7 | acc T=0 | acc T=0.7 | crude OR (CI) |
|---|---|---|---|---|---|
| qwen3:4b | 1052/1112 (0.946) | 722/752 (0.960) | 0.958 | 0.891 | 0.354 (0.243–0.514) |
| nemotron 9B | 459/888 (0.517) | 555/884 (0.628) | 0.692 | 0.651 | 0.832 (0.654–1.058) |
| champion 4B | 0/1200 | 0/720 | 0.893 | 0.879 | 0.870 (0.652–1.163) |
| qwen3:14b | 0/933 | 0/600 | 0.948 | 0.941 | 0.880 (0.562–1.378) |

- Rows that did not hit the cap: W18 crude OR 0.951 (0.757–1.195); design-stratified (model x relation x k) MH OR 0.895. The two models with zero cap hits: crude 0.886 (0.696–1.128), MH 0.827 (0.538–1.272).
- **The 0.69 outlier does not survive removal of cap-hit rows.** It is carried by qwen3:4b (all-rows MH 0.149), whose rows hit the cap 95.2% of the time (1774/1864) and are scored from visible reasoning — the same model paper.tex Sec. 2.2 already excludes as unauditable ("emitted its reasoning into the answer field").
- Reviewer's stated mechanism (higher T -> more truncation) holds for nemotron (0.517 -> 0.628) but not for qwen3:4b (0.946 vs 0.960, both near saturation). For qwen3:4b temperature and cap cannot be separated at all: only 72 of its rows did not hit the cap.
- The temperature arms are also unbalanced in design (e.g. champion 240 vs 144 rows per relation), so the per-wave crude OR mixes design as well.

Supports: "the W18 outlier is not a temperature effect we can attribute; it is confined to rows scored from length-capped output of a model we exclude elsewhere as unauditable." Does NOT support: "the one design where temperature may matter is exact-identifier recall under interference" (paper.tex 235-238; appendix.tex 166-170). Secondary: the "other three" in Sec. 2.3 include qwen3:4b, whose verdict-level non-answer rate is 1.45% (not <= 1%) while 95.2% of its responses hit the length cap.

## C. Leak attribution (PX8b objection 3) — **reviewer right**

Scripts: c1_leak_attribution.py (55e3b1561574) -> C_LEAK_RESULT_V1.json (f8ec9da629b6); c2_leak_k1_and_matched.py (1d5fb5031337) -> C_LEAK_K1_MATCHED_V1.json (ad9614c38297).

Calibration: reproduces 0.44 (W18 plain R4, champion: 169/384 = 0.4401) and 0.98 (W19 near_ids R4, champion: 106/108 = 0.9815) and the Appendix B table (k=1 0.000, k=3 0.900, k>=8 1.000). Known-bad: independent random ids give 0.000 at every k. Clopper-Pearson helper checked against known values.

Constraint: W19 rows log neither `truth` nor `others`, and item seeds use per-process `hash()` (MYTHOS_W18_ITEM_SEED_DEFECT_V1.json, 2677a8bc2a64), so item-level majority cannot be recomputed. Only k-level predictions are testable.

1. **At k >= 8 the mechanism is not identifiable from these logs.** Majority = gold for every generated item there, so "answered gold" and "answered the majority" are the same event. Champion: plain T=0 k>=8 29/156 (0.186) vs near_ids 72/72 (1.000).
2. **At the only k where the majority is certainly wrong (k=1: majority = the single distractor), the models do not follow it.** Champion 2/18 answered the majority (16/18 gold); qwen3:14b 3/11. Pooled over the two auditable models: 5/29 = 0.17 (CI95 0.06–0.36). Plain R4 at k=1 is also high (champion 41/42 at T=0), so at small k both conditions are solved by the recency/last-line reading. (qwen3:4b's near_ids R4 k=8 is 2/12 gold with 10 answering a distractor while the majority was gold, but its scoring is unauditable, so it is not used.)
3. At k=3 a majority-decoding model would miss ~10% of items; champion missed 0/18 (P = 0.15 under 10% misses, not decisive).
4. The headline compares different waves and arms: W18 plain pools T=0 and T=0.7 (T=0 only: 112/240 = 0.467); W19 near_ids ran only at T=0.

Supports: "the near-variant condition is solvable without the model (Appendix B), and in that condition model accuracy at k>=8 went to 72/72 where the plain condition gave 0.19; we cannot tell from these logs whether the model used the distractor set." Does NOT support "It is a leak" as an explanation of the jump; logged k=1 behaviour gives weak evidence against a pure majority-following reading.

---

## Ranked camera-ready change list

1. **Sec. 3 "Estimation" (paper.tex 171-180) and abstract (lines ~41-43).** Replace the estimator. Proposed: "Over-dispersion is estimated between repeats: for each design cell, the Pearson chi-square of repeat-group counts against the cell rate. Pooled over 166 design cells in seven waves phi = 1.08 (permutation p = 0.17); this design detects phi >= 1.25 with ~0.98 power." Delete "phi = 1.01 across eight waves", "binomial to within 5%", "no detectable drift, seed-dependent instability, or contamination". Evidence: A findings 1, 2, 4.
2. **Add a sentence reporting the flaw (Sec. 3 or Sec. 5, as a fourth case of the paper's own family).** Proposed: "Our first estimator computed within-cell Bernoulli variance, which equals n/(n-1) for any binary data; it returned ~1 by construction and could not have fired. A reviewer caught it." Evidence: A finding 1 (max deviation 2.1e-14 over 84 cells), injection 1.001–1.057.
3. **Appendix C (appendix.tex 105-131).** Replace the table with per-wave between-repeat phi, df, permutation p on design cells (0.68–1.15; wave 9: 1.131, p = 0.053) and the power row (0.52 at 1.10, 0.98 at 1.25). Change "eight waves" to "seven waves with an estimate". Evidence: A_PHI_FINE_PERMUTATION_V1.json, A_PHI_FINE_POWER_V1.json.
4. **Sec. 3 temperature paragraph (paper.tex 233-238) and Appendix D text (appendix.tex 166-170).** Remove the attribution to "exact-identifier recall". Proposed: "The one outlier (W18, OR 0.69) is carried by qwen3:4b, whose outputs hit the 160-token cap in 95% of rows and were scored from visible reasoning; without cap-hit rows W18 gives OR 0.95 (0.76–1.20), and the two models that never hit the cap give 0.89 (0.70–1.13). We cannot separate temperature from truncation in this wave." Evidence: B table and CIs.
5. **Sec. 2.1 (paper.tex 95-101).** Change "It is a leak" to "The condition leaks the answer", and state that attribution was not shown. Proposed: "Majority-voting the distractors reconstructs the gold string with no model. Whether the model exploited this we cannot establish from our logs: at k >= 8 majority and gold coincide on every item, and at k = 1, where the majority is wrong, the models answered gold in 24 of 29 cases." Evidence: C findings 1-2.
6. **Sec. 2.3 (paper.tex 151-157).** Narrow "the other three" and "<= 1%". Proposed: "... against at most 1.5% for the other three by verdict; one of them (qwen3:4b, excluded in Sec. 2.2) nevertheless hit the length cap in 95% of responses and was scored from visible reasoning, a milder form of the same failure." Evidence: B_SEC23_CAP_V1.json.
7. **Sec. 2.1 headline numbers.** Add the arm match: "0.44 (W18, T=0 and 0.7 pooled; 0.47 at T=0) to 0.98 (W19, T=0, n = 108)". Evidence: C finding 4.
8. **Limitations (paper.tex ~285-290).** Add: W18/W19 item seeds are not reproducible (per-process hash), and truth/distractors were not logged, so item-level re-analysis is impossible; this bounds objection C permanently for these waves. Evidence: MYTHOS_W18_ITEM_SEED_DEFECT_V1.json; C constraint.
9. **Response-to-reviews note.** Concede objections 1–3 as stated; the diagnostic half (Sec. 2.1 solvability, 2.2, 2.3) and the 2-SE calibration table are unaffected.

## What was not checked

- Corpus-wide "46,279 pairs / 17.3% readable / 639 pairs" was not recomputed (script not located); with phi ~ 1 it is a 2-SE enumeration either way.
- No item-level test of the leak mechanism is possible from frozen logs; a decisive test (distractors whose majority differs from gold at k >= 8) would need a new run, which was out of scope.
- Rows written after the cutoff were not used.
- The between-repeat power figures come from a Beta-binomial generator on repeat groups; other forms of dependence (drift within a repeat, item-by-repeat interaction) were not simulated.
