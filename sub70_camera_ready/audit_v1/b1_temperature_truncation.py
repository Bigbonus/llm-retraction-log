# -*- coding: utf-8 -*-
"""Objection B: is the wave-18 temperature outlier separable from truncation?

 1. CALIBRATE: re-implement mythos_cross_wave_v1.py (factor=temperature,
    min-cell 10) and reproduce Appendix D (W18 OR 0.69, 1/var 178.3; pooled
    OR 0.957 [0.905, 1.011], k 16, I2 44%, tau2 0.0046).
 2. KNOWN-BAD: (a) cutoff removed, (b) non-events counted as failures -> the
    reproduction check must report the difference.
 3. W18 stratified by length-cap status: done_reason == "length" (cap hit,
    visible or not), and eval_count >= num_predict; per temperature and model.
 4. W18 OR within rows that did NOT hit the cap; model-stratified
    Mantel-Haenszel OR (the pooled per-wave OR mixes models).
Writes B_TEMP_TRUNC_RESULT_V1.json."""
from __future__ import annotations

import collections
import datetime as dt
import math
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, __file__.rsplit("\\", 1)[0])
import audit_common as C  # noqa: E402

W18 = "mythos_relation_wave18_v1.jsonl"
PAPER_W18 = (0.69, 178.3)
PAPER_POOLED = {"OR": 0.957, "lo": 0.905, "hi": 1.011, "k": 16, "I2": 44, "tau2": 0.0046}
FAR = dt.datetime.fromisoformat("2100-01-01T00:00:00")


def outcome(r, nonevent_as_fail=False):
    v = r.get("verdict")
    if v in C.NON_EVENT:
        return False if (nonevent_as_fail and v is not None and v != "") else None
    c = r.get("correct")
    if isinstance(c, bool):
        return c
    if v is not None:
        return v in ("USED_LATEST", "CORRECT", "OK", "PASS")
    return None


def log_or(a, b, c, d):
    if min(a, b, c, d) == 0:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    return math.log((a * d) / (b * c)), 1 / a + 1 / b + 1 / c + 1 / d


def pool(rows):
    w = [1 / v for _, v in rows]
    fe = sum(x * wi for (x, _), wi in zip(rows, w)) / sum(w)
    Q = sum(wi * (x - fe) ** 2 for (x, _), wi in zip(rows, w))
    k = len(rows)
    c = sum(w) - sum(wi ** 2 for wi in w) / sum(w)
    tau2 = max(0.0, (Q - (k - 1)) / c) if c > 0 else 0.0
    w2 = [1 / (v + tau2) for _, v in rows]
    re_ = sum(x * wi for (x, _), wi in zip(rows, w2)) / sum(w2)
    se = math.sqrt(1 / sum(w2))
    I2 = max(0.0, (Q - (k - 1)) / Q) * 100 if Q > 0 else 0.0
    return re_, se, Q, I2, tau2, k


def cross_wave(cutoff, nonevent_as_fail=False, min_cell=10):
    per = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    for p in C.wave_files():
        for r in C.load(p.name, cutoff=cutoff):
            if "temperature" not in r:
                continue
            ok = outcome(r, nonevent_as_fail)
            if ok is None:
                continue
            per[p.name][r["temperature"]][1] += 1
            per[p.name][r["temperature"]][0] += bool(ok)
    studies = {}
    for wave, lv in per.items():
        usable = [k for k in sorted(lv, key=str) if lv[k][1] >= min_cell]
        if len(usable) == 2:
            (o1, n1), (o2, n2) = lv[usable[0]], lv[usable[1]]
            studies[wave] = log_or(o2, n2 - o2, o1, n1 - o1)
    re_, se, Q, I2, tau2, k = pool(list(studies.values()))
    return studies, {"OR": math.exp(re_), "lo": math.exp(re_ - 1.96 * se),
                     "hi": math.exp(re_ + 1.96 * se), "k": k, "I2": I2, "tau2": tau2}


def fmt_pool(d):
    return "OR %.3f [%.3f, %.3f] k %d I2 %.0f%% tau2 %.4f" % (d["OR"], d["lo"], d["hi"], d["k"],
                                                             d["I2"], d["tau2"])


def mh(strata):
    """Mantel-Haenszel OR over 2x2 strata (a,b,c,d) = (t07 ok, t07 fail, t0 ok, t0 fail)."""
    num = sum(a * d / (a + b + c + d) for a, b, c, d in strata if a + b + c + d)
    den = sum(b * c / (a + b + c + d) for a, b, c, d in strata if a + b + c + d)
    return num / den if den else None


def main() -> int:
    res = {"id": "SUB70_AUDIT_B_TEMP_TRUNC_V1", "w18_sha256": C.sha256_file(C.SRC / W18)}
    print("### 1. reproduce Appendix D")
    st, pooled = cross_wave(C.CUTOFF)
    lo, var = st[W18]
    got = (round(math.exp(lo), 2), round(1 / var, 1))
    ok1 = got == PAPER_W18
    ok2 = (round(pooled["OR"], 3) == PAPER_POOLED["OR"] and round(pooled["lo"], 3) == PAPER_POOLED["lo"]
           and round(pooled["hi"], 3) == PAPER_POOLED["hi"] and pooled["k"] == PAPER_POOLED["k"]
           and round(pooled["I2"]) == PAPER_POOLED["I2"] and round(pooled["tau2"], 4) == PAPER_POOLED["tau2"])
    print("  W18 paper %s recomputed %s %s" % (PAPER_W18, got, "OK" if ok1 else "MISMATCH"))
    print("  pooled recomputed %s  %s" % (fmt_pool(pooled), "OK" if ok2 else "MISMATCH"))
    res["calibration"] = {"w18": got, "pooled": pooled, "match": ok1 and ok2,
                          "per_wave_OR": {k: round(math.exp(v[0]), 3) for k, v in st.items()}}

    print("\n### 2. known-bad inputs")
    st_b, pooled_b = cross_wave(FAR)
    st_c, pooled_c = cross_wave(C.CUTOFF, nonevent_as_fail=True)
    kb = {"no_cutoff": {"w18_OR": round(math.exp(st_b[W18][0]), 3), "pooled": pooled_b},
          "nonevents_as_failures": {"w18_OR": round(math.exp(st_c[W18][0]), 3), "pooled": pooled_c}}
    for k, v in kb.items():
        print("  %-22s W18 OR %.3f | %s | reproduces paper: %s"
              % (k, v["w18_OR"], fmt_pool(v["pooled"]),
                 round(v["w18_OR"], 2) == PAPER_W18[0] and round(v["pooled"]["OR"], 3) == PAPER_POOLED["OR"]))
    res["known_bad"] = kb

    print("\n### 3. W18 by temperature x model: cap hits and accuracy")
    rows = C.load(W18)
    tab = collections.defaultdict(collections.Counter)
    for r in rows:
        t = r.get("temperature")
        m = r.get("model")
        npred = (r.get("options") or {}).get("num_predict") or r.get("num_predict")
        cap = r.get("done_reason") == "length"
        atcap = (r.get("eval_count") is not None and npred is not None and r["eval_count"] >= npred)
        ok = outcome(r)
        key = (m, t)
        tab[key]["rows"] += 1
        tab[key]["cap_len"] += cap
        tab[key]["eval_ge_cap"] += atcap
        tab[key]["trunc_novis"] += r.get("verdict") == "TRUNCATED_NO_VISIBLE_OUTPUT"
        tab[key]["error"] += r.get("verdict") == "ERROR"
        if ok is not None:
            tab[key]["scored"] += 1
            tab[key]["ok"] += bool(ok)
            if cap:
                tab[key]["scored_cap"] += 1
                tab[key]["ok_cap"] += bool(ok)
            else:
                tab[key]["scored_nocap"] += 1
                tab[key]["ok_nocap"] += bool(ok)
        tab[key]["dr_" + str(r.get("done_reason"))] += 1
    out3 = {}
    for (m, t), c in sorted(tab.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        d = dict(c)
        d["acc_scored"] = round(c["ok"] / c["scored"], 4) if c["scored"] else None
        d["acc_nocap"] = round(c["ok_nocap"] / c["scored_nocap"], 4) if c["scored_nocap"] else None
        d["cap_rate"] = round(c["cap_len"] / c["rows"], 4)
        out3["%s|%s" % (m, t)] = d
        print("  %-34s T=%-4s rows %5d cap %5d (%.3f) trunc_novis %4d | acc scored %s  acc no-cap %s (n %d)"
              % (m, t, c["rows"], c["cap_len"], d["cap_rate"], c["trunc_novis"], d["acc_scored"],
                 d["acc_nocap"], c["scored_nocap"]))
    res["w18_table"] = out3

    print("\n### 4. W18 OR: all scored, no-cap only, model-stratified")
    temps = sorted({t for (_, t) in tab}, key=str)
    res["w18_temps"] = temps
    if len(temps) == 2:
        t0, t1 = temps

        def agg(keyok, keyn, models=None):
            a = sum(tab[(m, t1)][keyok] for (m, t) in tab if t == t1 and (models is None or m in models))
            n1 = sum(tab[(m, t1)][keyn] for (m, t) in tab if t == t1 and (models is None or m in models))
            c = sum(tab[(m, t0)][keyok] for (m, t) in tab if t == t0 and (models is None or m in models))
            n0 = sum(tab[(m, t0)][keyn] for (m, t) in tab if t == t0 and (models is None or m in models))
            return a, n1 - a, c, n0 - c

        both = [m for m in {m for (m, _) in tab} if tab[(m, t0)]["scored"] >= 10 and tab[(m, t1)]["scored"] >= 10]
        out4 = {"models_with_both_temps": sorted(both)}
        for label, ko, kn in (("all_scored", "ok", "scored"), ("no_cap", "ok_nocap", "scored_nocap")):
            a, b, c, d = agg(ko, kn)
            lo_, var_ = log_or(a, b, c, d)
            strata = [(tab[(m, t1)][ko], tab[(m, t1)][kn] - tab[(m, t1)][ko],
                       tab[(m, t0)][ko], tab[(m, t0)][kn] - tab[(m, t0)][ko]) for m in both]
            a2, b2, c2, d2 = agg(ko, kn, set(both))
            lo2, _ = log_or(a2, b2, c2, d2)
            out4[label] = {"crude_OR_all_models": round(math.exp(lo_), 3),
                           "crude_CI": [round(math.exp(lo_ - 1.96 * math.sqrt(var_)), 3),
                                        round(math.exp(lo_ + 1.96 * math.sqrt(var_)), 3)],
                           "crude_OR_models_with_both": round(math.exp(lo2), 3),
                           "MH_OR_by_model": round(mh(strata), 3) if mh(strata) else None,
                           "per_model_OR": {m: round(math.exp(log_or(*s)[0]), 3) for m, s in zip(both, strata)},
                           "per_model_n": {m: (s[0] + s[1], s[2] + s[3]) for m, s in zip(both, strata)}}
            print("  %-10s %s" % (label, out4[label]))
        res["w18_or"] = out4
    p = C.write_json("B_TEMP_TRUNC_RESULT_V1.json", res)
    print("\nwrote", p)
    return 0 if res["calibration"]["match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
