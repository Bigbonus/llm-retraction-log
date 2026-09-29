# -*- coding: utf-8 -*-
"""Objection B, part 3: confidence intervals (Robins-Breslow-Greenland) for
the design-stratified Mantel-Haenszel OR in W18, and crude ORs with Woolf CI,
for the model subsets that never hit the length cap. Calibrated on a
textbook-style check: identical arms must give OR 1 and a CI covering 1;
a constructed strong effect must exclude 1.
Writes B_W18_MH_CI_V1.json."""
from __future__ import annotations

import collections
import math
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, __file__.rsplit("\\", 1)[0])
import audit_common as C  # noqa: E402
from b1_temperature_truncation import W18, log_or, outcome  # noqa: E402


def mh_rbg(strata):
    R = S_ = PR = PS_QR = QS = 0.0
    for a, b, c, d in strata:
        n = a + b + c + d
        if not n:
            continue
        r, s = a * d / n, b * c / n
        P, Q = (a + d) / n, (b + c) / n
        R += r
        S_ += s
        PR += P * r
        PS_QR += P * s + Q * r
        QS += Q * s
    orv = R / S_
    var = PR / (2 * R * R) + PS_QR / (2 * R * S_) + QS / (2 * S_ * S_)
    se = math.sqrt(var)
    return orv, math.exp(math.log(orv) - 1.96 * se), math.exp(math.log(orv) + 1.96 * se)


# calibration
null = [(40, 10, 40, 10)] * 5
strong = [(10, 40, 40, 10)] * 5
cn, cs = mh_rbg(null), mh_rbg(strong)
assert abs(cn[0] - 1) < 1e-9 and cn[1] < 1 < cn[2], cn
assert cs[2] < 1, cs
print("calibration null", [round(x, 3) for x in cn], "strong", [round(x, 3) for x in cs])

rows = C.load(W18)
S = collections.defaultdict(lambda: [0, 0, 0, 0])
for r in rows:
    ok = outcome(r)
    if ok is None:
        continue
    cap = r.get("done_reason") == "length"
    k = (r.get("model"), r.get("relation"), r.get("amount"), r.get("temperature"))
    S[k][0] += bool(ok)
    S[k][1] += 1
    if not cap:
        S[k][2] += bool(ok)
        S[k][3] += 1
res = {"id": "SUB70_AUDIT_B_W18_MH_CI_V1", "calibration": {"null": cn, "strong": cs}, "rows": {}}
subsets = {"champion+14b": ("mythos-4b-champion:q4km", "qwen3:14b"),
           "champion": ("mythos-4b-champion:q4km",), "qwen3:14b": ("qwen3:14b",),
           "nemotron9b": ("mythos-nemotron-nano-9b-v2:q5km",), "qwen3:4b": ("qwen3:4b",)}
for label, (io, in_) in (("all_scored", (0, 1)), ("no_cap", (2, 3))):
    for name, ms in subsets.items():
        st = []
        A = B = Cc = D = 0
        for k in {k[:3] for k in S}:
            if k[0] not in ms:
                continue
            x1, x0 = S[k + (0.7,)], S[k + (0.0,)]
            if x1[in_] and x0[in_]:
                st.append((x1[io], x1[in_] - x1[io], x0[io], x0[in_] - x0[io]))
                A += x1[io]
                B += x1[in_] - x1[io]
                Cc += x0[io]
                D += x0[in_] - x0[io]
        if not st or not (A + B) or not (Cc + D):
            continue
        try:
            m = mh_rbg(st)
        except ZeroDivisionError:
            m = None
        lo, var = log_or(A, B, Cc, D)
        crude = (math.exp(lo), math.exp(lo - 1.96 * math.sqrt(var)), math.exp(lo + 1.96 * math.sqrt(var)))
        res["rows"]["%s|%s" % (label, name)] = {
            "MH_OR_CI": None if m is None else [round(x, 3) for x in m],
            "crude_OR_CI": [round(x, 3) for x in crude],
            "n_T0.7": A + B, "n_T0": Cc + D, "acc_T0.7": round(A / (A + B), 4),
            "acc_T0": round(Cc / (Cc + D), 4)}
        print("%-10s %-13s %s" % (label, name, res["rows"]["%s|%s" % (label, name)]))
print("wrote", C.write_json("B_W18_MH_CI_V1.json", res))
