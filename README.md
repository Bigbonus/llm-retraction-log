# Eight Retractions in Twenty-Four Hours: A Log of What Broke While Measuring Small Language Models on One Home PC

**Version 1. 2026-08-21. This document is designed to grow; later versions add cases rather than replace them.**

---

## Abstract

Over roughly twenty-four hours of continuous measurement on a single consumer
GPU, eight claims I had written down were retracted. I kept the retractions in
a fixed schema at the moment each one died, including a field that cannot be
reconstructed afterwards: *why it looked true*.

Three of the eight were caused by **my own tools reporting something that had
not happened**. Three were caused by **changing the framing of a task and
watching the result reverse**. Two were caused by **stating a direction from a
single-digit sample**.

The pattern is not that small-scale research is sloppy. It is that at this
scale you are your own instrument-maker, and the instrument fails in ways that
look exactly like findings. I am publishing the log rather than the lessons,
because the lessons are short and the log is what makes them believable.

---

## 1. Why this exists

Negative results are underpublished for a well-known reason: they are not
rewarded. There is a second, less discussed reason. **The most useful part of
a retraction decays within hours.**

When a claim dies, the recoverable facts are what was claimed and what killed
it. What is *not* recoverable, a week later, is the answer to "why did this
look true at the time?" That answer is the only part that helps someone else
avoid the same error, because the error is never "I believed something
obviously false" — it is "I believed something that had every appearance of
being measured."

So the schema below has that field first, and the ledger is written the day
each claim dies.

## 2. Setting

One RTX 5080 (16 GB), 32 GB system RAM, Windows. Models: Qwen3 at 1.7B, 4B, 8B,
14B, plus a Nemotron Nano 9B, served through ollama 0.32.9 and through
transformers/peft directly. Roughly 25,000 measured rows across nineteen probe
waves, 135 LoRA adapters retained from earlier training runs, and a frozen
deterministic scorer.

Single operator. No lab, no second pair of eyes except an AI collaborator and,
late in the day, maintainers on a public issue tracker.

## 3. Schema

Each retraction records:

```
claim                what was asserted
why_it_looked_true   the appearance of evidence at the time   <- decays fastest
what_killed_it       the measurement that ended it
numbers              the figures on both sides
cost                 what was spent before noticing
generalizable        whether this is a shape others will hit
lesson               one line
```

## 4. The eight cases

### 4.1 Tools that reported something that had not happened

**Case A — a reproduction script reported a rejection for a request it never sent.**

The script measured whether a server silently truncates over-long prompts. It
built the request body by passing a 44 KB prompt to `jq` as a command-line
argument. On Windows the command line caps near 32 KB, so `jq` died, `curl`
sent an empty body, the server answered `400 {"error":"missing request body"}`,
and the script — seeing a 400 — printed:

```
verdict : REJECTED (prompt exceeded the served window)
```

*Why it looked true:* the expected status code arrived, from the expected
server, in the expected experiment.

*What killed it:* running it on the platform the paper was about. On Linux the
argument limit is ~2 MB and the bug never fires.

*Generalizable:* the tool built to demonstrate that instruments fabricate
phenomena was fabricating the phenomenon. The fix now requires the response
body to actually mention the context size before that verdict is allowed;
anything else reports `REQUEST FAILED` and the summary states plainly that
nothing was proved.

**Case B — a static checker for experiment code raised nine false findings.**

Two independent defects. It held the vocabulary of valid verdict names as an
**allowlist**, so a wave using different words was flagged as having a
degenerate scorer. And in

```python
reply, sec, verdict, correct, err = "", 0.0, "ERROR", False, msg
```

it collected every right-hand value when `verdict` appeared on the left,
counting the empty string as a verdict name and flagging seven files.

*Why it looked true:* the checker was written specifically to catch these
classes of error, so its output read as authority.

*Lesson:* **if everything passes, the checker is worthless; if everything
fails, the checker is broken.** Calibrate on known-good code before trusting a
single finding. After the fix: 13 pass, 2 exempt with an in-file declared
reason, 2 genuinely non-compliant — and those two turned out to predate the
provenance contract, independently corroborating an earlier quarantine
decision.

**Case C — an aggregation tool reported that zero paired cells existed.**

Comparing a base model against its distilled counterpart, the tool printed
`pairs: 0`. The stratification key was `science_epoch`, a fingerprint that
**includes the model name**. Base and student therefore always fall in
different epochs by construction, and requiring a shared epoch makes pairing
impossible.

*Why it looked true:* "0" from a working program reads as a fact about the
world.

*What killed it:* switching the pairing key to `instrument_epoch` (core +
runner) produced 85 cells.

*Lesson:* a zero from your own aggregator is a hypothesis about your key, not a
measurement of your data.

### 4.2 Framings that reversed the result

**Case D — "small models warn, large models lie."**

Sending an over-length prompt, a 4B and a 9B returned HTTP 400 with a clear
message; a 14B returned HTTP 200 with a silently truncated prompt and a
confident wrong answer. Three points, cleanly ordered by size.

*What killed it:* pulling a stock 4B of the same family. It truncates
identically to the 14B. The two that refuse are both GGUFs imported from
elsewhere. Swapping only the chat template on identical weights flips the
behaviour.

*Cost:* the framing reached a draft intended for publication. It was checked
before posting because the claim named a specific stock model tag that had
never been measured.

*Generalizable:* three points that happen to sit on your disk in a suggestive
order are not a mechanism. The relevant variable was invisible in the framing
that produced the observation.

**Case E — "interference is determined by type, not amount."**

A series of waves had shown that varying the number of same-format distractors
(1, 3, 8, 20) left a 4B at 0.00 throughout, while changing the *type* of
distractor moved it from 1.00 to 0.00 in a single step. This was the
highest-ranked proposition in the working ledger.

*What killed it:* rebuilding the measurement as a single ordinal ladder —
unrelated prose, same format, same field, same field unmarked, same field
repeatedly overwritten — with one harness, one scene generator, and one scoring
rule. Across three Qwen3 models and ~5,000 rows, the first four rungs sit at
1.00 up to eighty distractors. Only the overwrite rung degrades.

*Why it looked true:* the earlier task asked which of several records was the
answer. The new task names the field ("the latest attempt"). Same word —
"distractor" — different question.

*Generalizable:* this is the concrete form of a methodological complaint the
field has already voiced, that studies of context effects must state how they
distinguish signal from distractor or remain ambiguous between opposite
hypotheses. Our own strongest claim dissolved when a standardized ruler was
applied to it.

**Case F — a correction that itself needed correcting.**

Auditing published writing for instrument artifacts, I found that a baseline
model's outputs all sat at ~2,480 tokens with a spread of ten, i.e. pinned to a
generation ceiling. I concluded that describing the baseline as "unable to
finish" was a misattribution — it was budget truncation — and wrote that
correction into three manuscripts.

*What killed it:* the same dataset. **Not one of 130 baseline drafts stopped on
its own below the ceiling.** A model that never terminates does not benefit from
a larger budget. An independent measurement (stop-token log-mass, separating the
untrained from the trained checkpoint by +16.6 nat) pointed the same way.

*Why it looked true:* I had spent the day proving that instruments manufacture
apparent model deficits. The habit acquired a direction.

*Lesson:* **suspicion has a sign.** A day spent blaming the instrument creates
a bias toward blaming the instrument. The corrections were reissued the same
day; the direction of the original claim survived, only the attribution changed.

### 4.3 Directions asserted from single-digit samples

**Case G — instruction-update following.** Reported as improved by distillation
on n=3 (5/6 vs 2/6). At n≈144 the direction reverses (0.75 vs 0.95).

**Case H — a selective band in decoding-time steering.** At α≈2, general
capability appeared to drop while instruction-following and retrieval held —
which would have implied that an alignment tax can be separated at inference
time with no retraining. At n=12 the band is gone: everything collapses
together between α=1.2 and α=1.5.

*Both happened on the same day.* The second occurred after the first had been
recorded, which is the part worth reporting: writing the lesson down did not
prevent the repeat. What prevents it is a rule with a number in it — do not
state a direction below some fixed n — not an intention to be careful.

## 5. Distribution

```
Tools reporting non-events        3 / 8
Framing reversals                 3 / 8
Direction from small n            2 / 8
```

Three of eight — the largest single category — were not errors of inference at
all. They were programs printing conclusions about events that had not
occurred. Every one was written by the same person who then read its output as
evidence.

## 6. What this suggests for solo work

1. **Every instrument gets a control that must fail.** A checker that never
   fires on known-good input is uncalibrated. A battery where the treated and
   untreated conditions score identically cannot localize anything — we ran an
   ablation over layer groups and projection types before noticing that the
   full and fully-zeroed adapters scored the same on every item, which made the
   entire result unreadable.
2. **Non-events need their own vocabulary.** Separate `ERROR` and
   `TRUNCATED_NO_VISIBLE_OUTPUT` from any verdict that asserts a phenomenon,
   and forbid the substantive names inside exception handlers.
3. **A zero from your own tooling is a claim about your code.**
4. **Fix n before looking.** Both small-n reversals here were honest readings of
   real numbers.
5. **Watch the sign of your suspicion.** The correction that needed correcting
   came from a well-founded habit pointed one way for too long.
6. **Publish the number you cannot explain.** A figure we could not account for
   was answered within the hour by an upstream maintainer, from an issue filed
   in July that we had not known to search for.

## 7. Limitations

This is a log from one operator, one machine, one day, in one subfield. The
eight cases are the ones that died while records were being kept in this
schema; earlier retractions from the same project are not included because the
`why_it_looked_true` field was not captured at the time — which is itself the
argument for the schema.

No claim is made that these proportions generalize. The claim is narrower: at
this scale, tool-generated non-events are a failure mode of the same order as
statistical error, and they are not usually reported.

## 8. Availability

[`retractions.jsonl`](retractions.jsonl) holds the same eight cases in the
schema of section 3, one JSON object per line. It continues to accumulate.
Later versions of this document add cases; the case identifiers (A-H) are
stable and will not be reassigned.

Related: the measurement that produced cases A and D is written up separately,
with a runnable reproduction, at
<https://github.com/Bigbonus/ollama-context-window-check>, and was filed
upstream as ollama/ollama#17889.

---

*Written with an AI collaborator. All measurements were run on the machine
described; every figure in this document is from a recorded row, and the
retracted claims are quoted as they were originally written.*

---

## Author's note — not part of the paper

The program described in section 2 also produced two books. They are the same
machine and the same habit seen from the other side: what it takes to build and
keep the thing running, rather than what broke.

**Raising Your Own AI on a Home PC** — six months on the 16 GB consumer GPU
described above. It opens with the morning an AI told me *"Actually, that isn't
distillation."* I had spent half a year collecting 133 draft-and-correction
pairs as experience points for a student model whose weights had been updated
exactly zero times. It keeps the wiring mistakes, the scoring mistakes and the
failed predictions — including the run where the machine score improved while a
blinded human comparison gave the trained side 0 wins, 9 losses and 11 ties.
[Kindle $9.99](https://www.amazon.com/dp/B0HCT93JX3) ·
[Paperback $12.99](https://www.amazon.com/dp/B0HDPMNMTQ) ·
data at [10.5281/zenodo.21730423](https://doi.org/10.5281/zenodo.21730423)

**Applied AI Distillation: Make AI Yours** — five practical paths for adapting a
model to your own use, starting from a no-training baseline, with runnable
fixtures and known-answer tests.
[Kindle $9.99](https://www.amazon.com/dp/B0HFJNDJV6) ·
[Paperback $79.90](https://www.amazon.com/dp/B0HFKFZ5Q2)

**No claim in this log depends on either book, and neither is needed to
reproduce anything here.** The ledger, the schema and the eight cases stand on
their own and are CC BY 4.0.
