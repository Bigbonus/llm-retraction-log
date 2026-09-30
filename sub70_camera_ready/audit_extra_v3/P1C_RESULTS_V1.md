# P1-c results (Claude), run once under manifest 9f4a6a0bbc52

Runner p1c_run_v1.py 3f077c195d56; estimator between_repeat_phi_v3.py 20496faad331; protocol draft
86638721c85b; binding addendum af5b78320ad7. Started 08:02 JST, status **complete**, 45/45 points,
elapsed 6,208 s (103 min) on one worker, inside the 120-min stop. No dataset lacked a usable cell.
Raw: P1C_RESULTS_V1.json (7ba53c2624c6): per point counts, Wilson 95% intervals, every phi-hat and p.
Design as frozen: N = 100 datasets per point, NPERM = 1000, reject p < 0.05, seeds fixed in the
manifest. At N = 100 each rate has a Wilson interval about ±0.04–0.10 wide; nothing below is finer
than that.

## S1: independent-binomial null, rejection rate (target 0.05)

| C \ m | 4 | 8 | 12 |
|---|---|---|---|
| 20 | 0.02 [0.006, 0.070] | 0.03 [0.010, 0.085] | 0.03 [0.010, 0.085] |
| 60 | 0.04 [0.016, 0.098] | 0.05 [0.022, 0.112] | 0.06 [0.028, 0.125] |
| 166 | 0.07 [0.034, 0.138] | 0.07 [0.034, 0.138] | 0.06 [0.028, 0.125] |

All nine intervals contain 0.05. At C = 20 the point estimates sit below 0.05 (discrete permutation
p with 1,000 draws is conservative for small df); at C = 166 they sit above (0.06–0.07). With N = 100
this is not evidence of miscalibration either way, and it is not proof of calibration; it says the
test's null rejection is not far from nominal at these sizes.

## S2: power against between-repeat Beta-binomial excess (the tested alternative)

| phi_true | C=20, m 4/8/12 | C=60, m 4/8/12 | C=166, m 4/8/12 |
|---|---|---|---|
| 1.10 | 0.16 / 0.18 / 0.21 | 0.32 / 0.24 / 0.23 | 0.51 / 0.54 / 0.40 |
| 1.25 | 0.41 / 0.40 / 0.34 | 0.83 / 0.74 / 0.78 | 1.00 / 0.99 / 0.99 |
| 1.50 | 0.90 / 0.80 / 0.84 | 1.00 / 1.00 / 0.99 | 1.00 / 1.00 / 1.00 |

Intervals in the JSON (width about ±0.10 at mid-range). At the paper's cell count (166) the values
match Appendix C's earlier simulation (0.52 at 1.10, 0.98 at 1.25) within the intervals. At 20
cells the test has little power below phi 1.5. Power depends on the number of cells far more than
on rows per repeat in this range.

## S3: shared-item stress test (items reused across repeats, no repeat effect)

| C \ m | 4 | 8 | 12 |
|---|---|---|---|
| 20 | 0.02 | 0.01 | 0.00 |
| 60 | 0.00 | 0.00 | 0.01 |
| 166 | 0.00 | 0.00 | 0.00 |

Every Wilson upper bound is <= 0.07 and seven of nine points have upper bound 0.037. Under this
generator repeat counts are *less* variable than binomial (conditional variance sum d_i(1-d_i),
0.8 m p(1-p) in expectation), so the unrestricted within-cell shuffle makes the test conservative:
it rejects less than 5% of the time. Direction was not predicted; this is the measured direction.
It is a stress-test rejection rate, not a false-positive rate (the S1 null is not the DGP) and not
power (no between-repeat effect was injected).

## What this changes in the paper's claims

1. Appendix C's power figures (0.98 at 1.25, 0.52 at 1.10) stand for the 166-cell design under the
   Beta-binomial alternative. No correction.
2. New stated limit: **when repeats reuse the same items, the between-repeat test becomes
   conservative** (S3: 0–2% rejection at the null). It does not manufacture excess dispersion, but
   its power under item reuse was not measured and is expected to be lower than S2. The paper's
   waves do not log item reuse in every wave, so this limit applies to phi = 1.08 itself: the
   observed non-detection is consistent with either no excess or excess masked by reuse.
3. At small cell counts (about 20) the test has little power below phi 1.5; readers with small logs
   should not read a non-rejection as evidence of binomial repeats.

## Proposed Appendix C sentence (V7)

"A calibration run (45 design points, 100 datasets each, settings frozen before execution and
released with the audit files) gave null rejection rates of 0.02–0.07 across 20–166 cells, power
0.40–0.54 at phi = 1.10 and 0.99–1.00 at 1.25 for 166 cells, and 0.00–0.02 rejection when items
were reused across repeats without a repeat effect: with item reuse the test is conservative, and
its power in that setting was not measured."

## Limits of this run

One seed set, N = 100 per point, one alternative family (Beta-binomial), one reuse generator
(Beta(4p, 4(1-p)) item difficulties, R = 4). Serial drift and item-by-repeat interaction were not
simulated. Same machine and implementer as the estimator.
