# G1 and G2 results, V2 (Claude), correcting V1 per SUB70_G1_G2_INTERPRETATION_REVIEW_V1

V1 files are kept unchanged. This version supersedes their interpretation; see CORRECTION_NOTE_V1.md
for what V1 said and why it was wrong. Frozen rows only, the seven Appendix C waves, no model.

## G1 V2: `between_repeat_phi_v2.py`

- Malformed input is refused with line numbers (blank cell or repeat, `correct` outside the accepted
  set, missing column), exit 2, no number printed. Excluded cells are counted by reason and printed.
- `test_between_repeat_phi_v2.py`: 9 negative and accounting tests, all pass. The same malformed
  files are accepted by V1 and produce a number from fewer rows; the tests show that too.
- Smoke test (one seed, not an error-rate estimate): binomial fixture phi 0.892, p 0.894; injected
  phi_true 2.0 gives phi 1.809, p 0.001. PASS. Codex reproduced these independently.
- Parity: the exported paper cells (31,938 rows, 714 cells given, 548 excluded for rate 0 or 1)
  give 166 cells, df 1,424, phi 1.076, permutation p 0.164 — equal to Appendix C.
- Stated in the file: the three-column format cannot verify item re-use across repeats,
  exchangeability, or that two cells are the same condition. The permutation p is valid only under
  exchangeability. Non-events must be excluded before the CSV is written.

## G2 V2: `g2_readable_flag_rate_v2.py` (rule fixed before analysis: 2 sqrt(1.08 (0.25/n1 + 0.25/n2)))

Cells with a repeat of >= 4 rows and pooled rate inside (0, 1): 5 waves, 120 cells, 1,565 pairs.
Waves 2 and 3 have no repeat with >= 4 rows and contribute nothing.

| measure | what it is | n 4–7 | n 8–15 | all |
|---|---|---|---|---|
| A. within-condition flag rate | rule fired on two repeats with the same design label | 0.008 (1,082 pairs) | 0.000 (483) | 0.0058 (1,565) |
| A. shuffled-outcome rate | same pairs, outcomes shuffled across the two repeats, 200x | 0.012 | 0.007 | 0.0101 |
| B. fixture | second count set to round((p1 ± 0.5) n2); realized mean diff 0.50 | 0.111 | 0.557 | 0.249 |
| C. power, (0.25, 0.75), MC at real sizes | 400 binomial draws per pair, both arms | 0.35 | 0.54 | 0.41 |
| C. power, (0.40, 0.90) | same | 0.34 | 0.54 | 0.40 |
| C. power, (0.50, 0.80) | same | 0.12 | 0.18 | 0.14 |

Monte Carlo SE of each C figure is <= 0.001 (>= 190,000 draws per bin).

What each row means, and no more:
- A is a within-condition flag rate. Equal design labels do not prove equal outcome distributions,
  so it is not an established false-positive rate. It sits at about the shuffled rate; the shuffled
  rate is a null only if individual outcomes are exchangeable across repeats, which these logs do
  not establish (item re-use is not logged in every wave). Pairs share rows, items, cells and
  waves; none of these is an independent-sample figure.
- B is a deterministic fixture. The rule fired on 25% of perturbed pairs whose realized difference
  averaged 0.50. It is not power, and V1's "misses a 0.5 shift 89% of the time" is withdrawn.
- C is the only power figure. For two binomial arms at 0.25 and 0.75, at the repeat sizes this
  programme actually has, the rule flags 41% of draws; at 0.50 vs 0.80 it flags 14%. These are for
  the three preregistered pairs at these sizes and nothing else.
- phi = 1.08 was estimated from these same repeats; this calibrates the rule given phi, not phi.

## Proposed App C text, V2 (not applied)

"A schema-free implementation of the estimator, with refusal of malformed rows and a self-test, is
released with the audit files; on the 166 design cells it reproduces phi = 1.08 exactly. On 1,565
pairs of repeats carrying the same design label the readable rule fired on 0.6% (1.0% with outcomes
shuffled across the pair); for two binomial arms at 0.25 and 0.75 drawn at the same pair sizes it
fires on 41% (35% where repeats have 4–7 rows). The floor is coarse at these repeat sizes: that is
the rule refusing to read small-n differences, and its cost."

## G3 wording, V2 (not applied), per Codex: the particular observed miss

Sec. 2.3, after "a milder form of the same failure": "The verdict-distribution check did not fire on
that model: its outputs hit the cap in 95.2% of rows yet contained text, so they were scored. The
check catches empty output; in this wave it missed capped output that still contained text, and its
silence on a model is not evidence that the model was unaffected." Sec. 4 item 2: "There is no
detector for this class in our harness; it was found by reading."
