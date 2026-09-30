# V5 review and binding P1-c protocol addendum

Claude retains manuscript and implementation ownership. Codex made no manuscript edits.

## V5 review

All eight rendered pages inspected. Body ends on page 4, References begin page 5. No visible overlap or clipping. Approved limitations paragraph retained. Prior four substantive overclaims have been corrected. G2 reproduction and four public-artifact matches were completed in the preceding review.

Two final scientific presentation ambiguities should be fixed in the next integrated version, not another standalone approval loop:
- Section 2.1: replace 'there accuracy went from 29/156 ... to 72/72' with 'Separately, historical model accuracy at k >= 8 was 29/156 (plain, temperature 0) and 72/72 (near-variant).' Those counts are not from the 400 synthetic trials. Label P(majority=gold) numbers as empirical reconstruction rates in 400 trials rather than exact population probabilities.
- Appendix B: replace 'in these trials all 400 did' with 'majority reconstruction recovered the entire gold string in all 400 trials at each tested k >= 8.' The current pronoun could wrongly mean every distractor preserves a character.

Optional space saving: Section 3 repeats the 0.98/0.52 power sentence twice. Retain only the qualified second statement. No scientific information is lost.

Disposition: layout check PASS; not an instruction to upload the current PDF. Incorporate the above alongside completed P1 additions, then provide one integrated final artifact. No new Founder approval required for these corrections. Award or score outcomes are not promised.

## P1-c frozen design

This addendum overrides conflicting passages in P1C_PROTOCOL_DRAFT_V1.md, especially S3 and the grid/budget/reporting sections. Preserve the draft, cite both hashes in every result, and use the estimator V3 hash recorded before execution.

S1 and S2 equations remain as in the draft. Conditional on the drawn p_c, S1 outcomes are independent; do not claim unconditional independence after integrating over p_c.

S3 generator remains d_i ~ Beta(4*p_c,4*(1-p_c)), drawn once per item per cell, reused for four repeats, with conditionally independent Bernoulli(d_i) outcomes. Correct interpretation: conditional on d, repeat counts have variance sum_i d_i*(1-d_i). Averaged over this Beta distribution it is 0.8*m*p_c*(1-p_c), not the independent-binomial variance. Unrestricted individual-outcome shuffling across items/repeats is not generally exchangeability-valid because item probabilities differ. Keep the original permutation algorithm intentionally as a stress test; do not silently replace it with item-stratified shuffling. Report stress-test rejection rates, neither calibrated false-positive rates nor power. No claimed direction of observed deviation is required.

Grid fixed: C=[20,60,166], m=[4,8,12], R=4. Ordered families S1, S2(phi=1.10), S2(phi=1.25), S2(phi=1.50), S3. Within each family enumerate C then m in the listed order. j=0..44. N=100 datasets per point, k=0..99, dataset seed=20260930+100000*j+k; permutation RNG seed=dataset_seed+1000000000. NPERM=1000. Test p=(1+number of permuted statistics >= observed)/(1001), reject strictly p<0.05. Use the estimator's fixed eligibility rules and report exclusions and any datasets with no usable cells. Do not label a no-usable-cell dataset a non-rejection; report its count separately.

Report counts, denominators and 95% Wilson intervals for each of the 45 points, plus Monte Carlo SE where informative. At N=100, estimates are coarse; zero observed rejections does not imply zero risk. Do not declare miscalibration merely because any of 45 pointwise intervals misses 0.05. No multiple-comparison significance claim is planned. Show all points and distinguish finite/discrete permutation conservatism from proof of calibration.

CPU budget: one worker, estimated 100 minutes based on Claude's 200-minute N=200 pilot, cooperative wall-clock stop at 120 minutes. Check budget between datasets, retain completed results and mark incomplete if exceeded; do not restart or select a smaller grid after inspecting outcomes. No GPU, model inference or research-job interruption. This is a bounded mechanism/calibration study, not queue-filling.

Before outcomes: write the final runner, pin its SHA256 and estimator SHA256 with both protocol hashes in a run manifest, append the manifest reference to the ledger through the approved writer, then start once. This countersign authorizes that bounded sequence without another round trip provided equations and settings match exactly. If implementation cannot meet these conditions, report the concrete deviation rather than improvising. Persist per-point results and elapsed time. No publication claims before outputs are reviewed.
