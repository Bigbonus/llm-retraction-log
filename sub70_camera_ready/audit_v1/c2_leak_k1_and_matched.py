# -*- coding: utf-8 -*-
"""Objection C, part 2.
 (a) The only k at which position-wise majority is certainly WRONG is k=1
     (majority = the single distractor; P = 1.000 in c1's leak table). Count
     how often the model's answer equals the majority there (USED_OLDER at
     k=1 means the reply contains the one distractor = the majority).
     Clopper-Pearson 95% interval on the majority-following fraction.
 (b) At k >= 8 majority = gold for every generated item, so "answer = gold"
     and "answer = majority" are the same event: not identifiable.
 (c) Matched comparison for the 0.44 -> 0.98 headline: W18 plain R4 at T=0
     only (W19 near_ids ran only at T=0), per k.
Writes C_LEAK_K1_MATCHED_V1.json."""
from __future__ import annotations

import collections
import sys

from scipy import stats

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, __file__.rsplit("\\", 1)[0])
import audit_common as C  # noqa: E402
from c1_leak_attribution import W18, W19  # noqa: E402


def cp(x, n):
    lo = 0.0 if x == 0 else stats.beta.ppf(0.025, x, n - x + 1)
    hi = 1.0 if x == n else stats.beta.ppf(0.975, x + 1, n - x)
    return round(float(lo), 3), round(float(hi), 3)


# calibration of cp(): known values (0/10 upper ~0.308; 5/10 ~[0.187, 0.813])
assert cp(0, 10)[1] == 0.308 and cp(5, 10) == (0.187, 0.813), (cp(0, 10), cp(5, 10))

w18, w19 = C.load(W18), C.load(W19)
res = {"id": "SUB70_AUDIT_C_K1_MATCHED_V1", "k1": {}, "matched": {}}
print("### (a) near_ids R4, k=1: answer = majority (= the distractor) vs gold")
for m in ("mythos-4b-champion:q4km", "qwen3:14b", "qwen3:4b"):
    c = collections.Counter(r.get("verdict") for r in w19
                            if r.get("hard") == "near_ids" and r.get("relation") == "R4_overwrite"
                            and r.get("amount") == 1 and r.get("model") == m)
    n = sum(v for k, v in c.items() if k not in C.NON_EVENT)
    res["k1"][m] = {"verdicts": dict(c), "scored": n, "gold": c["USED_LATEST"],
                    "majority_followed": c["USED_OLDER"],
                    "majority_followed_CI95": cp(c["USED_OLDER"], n) if n else None}
    print("  %-26s %s" % (m, res["k1"][m]))
x = res["k1"]["mythos-4b-champion:q4km"]["majority_followed"] + res["k1"]["qwen3:14b"]["majority_followed"]
n = res["k1"]["mythos-4b-champion:q4km"]["scored"] + res["k1"]["qwen3:14b"]["scored"]
res["k1"]["auditable_two_models"] = {"majority_followed": x, "scored": n, "CI95": cp(x, n)}
print("  auditable two models pooled: %d/%d follow majority, CI95 %s" % (x, n, cp(x, n)))

print("\n### (c) matched headline: champion R4, T=0 only")
for src, rows, cond in (("W18_plain_T0", w18, None), ("W18_plain_allT", w18, "all"),
                        ("W19_near_ids_T0", w19, "near_ids")):
    per = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        if r.get("model") != "mythos-4b-champion:q4km" or r.get("relation") != "R4_overwrite":
            continue
        if cond == "near_ids" and r.get("hard") != "near_ids":
            continue
        if cond is None and r.get("temperature") != 0.0:
            continue
        if r.get("verdict") in C.NON_EVENT:
            continue
        per[r.get("amount")][1] += 1
        per[r.get("amount")][0] += r.get("verdict") == "USED_LATEST"
    tot = [sum(v[0] for v in per.values()), sum(v[1] for v in per.values())]
    ge8 = [sum(v[0] for k, v in per.items() if k >= 8), sum(v[1] for k, v in per.items() if k >= 8)]
    res["matched"][src] = {"per_k": {k: v for k, v in sorted(per.items())}, "all": tot,
                           "acc_all": round(tot[0] / tot[1], 4), "k_ge_8": ge8,
                           "acc_k_ge_8": round(ge8[0] / ge8[1], 4), "k_le_3":
                           [tot[0] - ge8[0], tot[1] - ge8[1]]}
    print("  %-16s %s" % (src, res["matched"][src]))
print("wrote", C.write_json("C_LEAK_K1_MATCHED_V1.json", res))
