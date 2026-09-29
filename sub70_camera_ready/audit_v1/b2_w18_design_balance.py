# -*- coding: utf-8 -*-
"""Objection B, part 2: are the two temperature arms of W18 the same design?
Composition by relation per (model, temperature), and Mantel-Haenszel OR
stratified by (model, relation, amount), for all scored rows and for rows
that did not hit the length cap. Also: cap-hit rate by temperature within
each model and relation (does temperature raise truncation?).
Writes B_W18_BALANCE_V1.json."""
from __future__ import annotations

import collections
import math
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, __file__.rsplit("\\", 1)[0])
import audit_common as C  # noqa: E402
from b1_temperature_truncation import W18, mh, outcome  # noqa: E402

rows = C.load(W18)
comp = collections.defaultdict(collections.Counter)
S = collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0])  # ok,n,ok_nocap,n_nocap,cap,rows
for r in rows:
    m, t = r.get("model"), r.get("temperature")
    comp[(m, t)][r.get("relation")] += 1
    ok = outcome(r)
    cap = r.get("done_reason") == "length"
    s = S[(m, r.get("relation"), r.get("amount"), t)]
    s[5] += 1
    s[4] += cap
    if ok is None:
        continue
    s[0] += bool(ok)
    s[1] += 1
    if not cap:
        s[2] += bool(ok)
        s[3] += 1

res = {"id": "SUB70_AUDIT_B_W18_BALANCE_V1", "composition": {}, "mh": {}, "cap_by_temp": {}}
print("### composition (rows by relation)")
for (m, t), c in sorted(comp.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
    res["composition"]["%s|%s" % (m, t)] = dict(c)
    print("  %-34s T=%s %s" % (str(m)[:34], t, dict(sorted(c.items()))))

temps = sorted({k[3] for k in S}, key=str)
t0, t1 = temps[0], temps[-1]
strata_keys = sorted({k[:3] for k in S}, key=str)
for label, io, in_ in (("all_scored", 0, 1), ("no_cap", 2, 3)):
    for msel in ("all_models", "champion+14b", "qwen3:4b", "nemotron9b"):
        st = []
        for sk in strata_keys:
            m = sk[0]
            if msel == "champion+14b" and m not in ("mythos-4b-champion:q4km", "qwen3:14b"):
                continue
            if msel == "qwen3:4b" and m != "qwen3:4b":
                continue
            if msel == "nemotron9b" and m != "mythos-nemotron-nano-9b-v2:q5km":
                continue
            a1, b1 = S[sk + (t1,)][io], S[sk + (t1,)][in_]
            a0, b0 = S[sk + (t0,)][io], S[sk + (t0,)][in_]
            if b1 and b0:
                st.append((a1, b1 - a1, a0, b0 - a0))
        orv = mh(st)
        n = sum(sum(x) for x in st)
        res["mh"]["%s|%s" % (label, msel)] = {"MH_OR": None if orv is None else round(orv, 3),
                                             "strata": len(st), "rows": n}
        print("  MH OR %-10s %-13s %s (strata %d, rows %d)" % (label, msel,
              None if orv is None else round(orv, 3), len(st), n))

print("\n### cap-hit rate by temperature, per model (rows in strata present at both temps)")
for m in sorted({k[0] for k in strata_keys}, key=str):
    c0 = n0 = c1 = n1 = 0
    for sk in strata_keys:
        if sk[0] != m or not S[sk + (t0,)][5] or not S[sk + (t1,)][5]:
            continue
        c0 += S[sk + (t0,)][4]
        n0 += S[sk + (t0,)][5]
        c1 += S[sk + (t1,)][4]
        n1 += S[sk + (t1,)][5]
    if n0 and n1:
        res["cap_by_temp"][m] = {"T0": [c0, n0, round(c0 / n0, 4)], "T0.7": [c1, n1, round(c1 / n1, 4)]}
        print("  %-34s T0 %d/%d (%.3f)  T0.7 %d/%d (%.3f)" % (m[:34], c0, n0, c0 / n0, c1, n1, c1 / n1))
print("wrote", C.write_json("B_W18_BALANCE_V1.json", res))
