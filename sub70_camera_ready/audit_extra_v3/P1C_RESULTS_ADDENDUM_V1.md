# P1-c results: correction addendum (Claude), per SUB70_V7_P1C_REVIEW_V1

P1C_RESULTS_V1.md and P1C_RESULTS_V1.json (7ba53c2624c6) are unchanged. This addendum corrects the
commentary; where they disagree, this file governs.

1. **Count correction.** S3 has six zero-rejection points, not seven; the other three points are
   2, 1 and 1 rejections out of 100. Six Wilson upper bounds round to 0.037. The JSON and the S3
   table were already correct; the sentence under the table was not.

2. **Scope of the reuse claim.** "With item reuse the test is conservative" is withdrawn as a
   general statement. What was measured: in one shared-item generator (d_i ~ Beta(4p, 4(1-p)),
   reused over R = 4 repeats, no repeat effect) on this grid, rejection was 0.00–0.02. Power under
   item reuse was not measured and is not claimed to be lower. That excess dispersion in the real
   logs could be masked by reuse is an unresolved possible explanation, not an established finding.

3. **Withdrawn attribution.** The V1 commentary attributed the below-0.05 point estimates at C = 20
   to the discreteness of the 1,000-draw permutation p at small df. That was not tested; sampling
   variability at N = 100 and other features were not separated. What stands: all nine S1 intervals
   are compatible with nominal rejection, which is not proof of calibration.

4. **Reading the saved p-values.** p is stored to four decimals. The exact value is
   (1 + #permuted >= observed) / 1001; to reconstruct the integer numerator, multiply the stored p
   by 1001 and round. Rejection used the exact value strictly below 0.05, so 50/1001 (stored as
   0.0500) is a rejection. The stored rejection counts were computed from the exact values and need
   no change.

Manuscript wording follows Codex's exact Appendix C text (V8), which limits the inference to the
simulated generators.
