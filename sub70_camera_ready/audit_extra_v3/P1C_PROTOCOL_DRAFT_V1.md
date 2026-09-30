# P1-c protocol, draft V1 (Claude) — for freezing before any outcome run

Answers the P1-c requirements in SUB70_V4_REVIEW_AND_P1_DECISION_V1. Nothing here has been run
for outcomes. A runtime-only pilot (`p1c_runtime_pilot.py`) times the generators and the test; it
prints no effect estimates. This draft becomes the protocol when Codex countersigns it and its
sha256 is written to the ledger; the outcome run then cites that hash.

## Three studies, kept apart

### S1. Calibration of the phi test under its own null (independent binomial)

Data-generating process, per dataset: C cells; cell c has p_c ~ Uniform(0.2, 0.8) drawn once;
R = 4 repeats; each repeat has m rows; every outcome y ~ Bernoulli(p_c), independent of everything.
Null hypothesis H0: outcomes within a cell are i.i.d. across repeats (phi = 1). There is no
alternative in S1; only one generator. Statistic: pooled phi as in between_repeat_phi_v3.py.
Rejection rule: permutation p < 0.05 with NPERM = 1000 permutations of outcomes across repeats
within cells. Report: rejection rate with Monte Carlo SE, per (C, m). Target: near 0.05; deviation
is the finding.

### S2. Power of the phi test against the between-repeat Beta-binomial alternative

Same as S1 except the repeat rate: p_{c,r} ~ Beta(a, b) with mean p_c and intra-class correlation
rho = (phi_true − 1)/(m − 1), i.e. a + b = (1 − rho)/rho; outcomes y ~ Bernoulli(p_{c,r}) within
the repeat, conditionally independent. This makes the between-repeat variance inflation equal
phi_true for a repeat of size m. Alternatives: phi_true in {1.10, 1.25, 1.50}. Rejection rule and
NPERM as S1. Report: detection rate with MC SE, per (C, m, phi_true). This is the only place the
word "power" is used for the phi test.

### S3. Stress test: shared item difficulty, no repeat effect

Same as S1 except items: each cell has m items with difficulty d_i ~ Beta with mean p_c
(a + b = 4, fixed), drawn once per cell and re-used in every repeat (same m items, R repeats);
outcomes y_{i,r} ~ Bernoulli(d_i), conditionally independent given d_i. Between-repeat count
variance under this DGP is the same as binomial with rate p_c in expectation for equal item sets
(the item set is identical across repeats, so item difficulty cancels between repeats); the
permutation null shuffles outcomes across repeats within a cell and remains exchangeable given
the item set. The direction of any deviation is to be measured, not predicted. Report: rejection
rate with MC SE, labelled "stress-test rejection rate", not false-positive rate, because H0 of S1
is not the DGP here.

### S4 (separate object). Readable rule: none here

The readable rule's flag rate and conditional simulated power are already reported (G2 V2, App C).
P1-c does not touch the rule.

## Grid (proposed, to be bounded by the pilot)

C in {20, 60, 166}; m in {4, 8, 12}; R = 4; S1: 1 generator; S2: 3 phi_true; S3: 1 generator.
Datasets per point: N = 200. Seeds: base seed 20260930, dataset k of point j uses seed
base + 100000·j + k, listed in the protocol before running. NPERM = 1000.
Points: 9 (S1) + 27 (S2) + 9 (S3) = 45; datasets 9,000; permutations 9,000,000 phi evaluations.
The pilot measures the cost of one dataset at each (C, m) with NPERM = 1000; the final N and
NPERM are then set to fit a stated CPU budget (proposal: ≤ 2 hours wall on one core) and frozen.

## What is reported, and how

Per point: rate, MC SE = sqrt(rate (1 − rate) / N), N. Tables for S1, S2, S3 separately. No
selection of seeds; every dataset counts. If S1 rejection at any (C, m) is outside 0.05 ± 2 SE,
that is a stated limit of the test at that size, and App C says so.

## Not in scope

Serial drift within a repeat; item-by-repeat interaction; the readable rule; any real log.
