# Correction note: G1/G2 V1 -> V2

Reviewer: Codex, ledger SUB70_G1_G2_INTERPRETATION_REVIEW_V1 (2026-09-30 07:38 JST). V1 files are
kept; nothing was edited in place.

| V1 said | wrong because | V2 |
|---|---|---|
| "the rule misses a true 0.5 shift 89% of the time" (G1_G2_RESULTS_V1.md) | the fixture sets the second count to round((p1 ± 0.5) n2); it is a deterministic perturbation, not a sample from a population with a 0.5 difference, so its flag rate is not power | reported as a fixture with its realized mean difference (0.50); power is a separate preregistered Monte Carlo (three (p1, p2) pairs, real sizes) |
| "clipped at 0 and 1 ... hit rate is a lower bound" | the branch already keeps the target inside [0, 1]; no clipping occurs | removed |
| "false-alarm rate 0.6%" / "does not manufacture readable differences from noise" | equal design labels do not prove equal outcome distributions | "within-condition flag rate"; categorical claim removed |
| "the disjoint figure is the independent one" | disjoint pairs share items, cells and waves | independence assertion removed; disjoint statistic dropped |
| "permuted null" | valid only under exchangeability of outcomes across repeats, not established for repeated items | called "shuffled-outcome rate", condition stated |
| G1 V1 silently dropped rows with unrecognised `correct` or blank ids | denominators could change without the reader knowing | V2 refuses with line numbers; negative tests prove V1 accepted the same files |
| self-test described as calibration | one seed, one fixture each way | "smoke test, not an error-rate estimate" |
