# -*- coding: utf-8 -*-
"""Objection A: is the paper's over-dispersion estimate a property of the
estimator or of the data?

Steps (all CPU, no model, read-only on the frozen logs):
 1. CALIBRATE: re-implement the paper's estimator (mythos_noise_floor_v1.py
    logic) and reproduce Appendix C (cells, mean cell n, phi) per wave.
 2. KNOWN-BAD: same code with the freeze cutoff removed must NOT reproduce
    Appendix C (the check must be able to fail).
 3. IDENTITY: per non-degenerate cell, compare the paper's cell statistic with
    n/(n-1).
 4. INJECTION on real cells: replace outcomes with maximally over-dispersed
    blocks (each repeat group all-0 or all-1) and re-run the paper estimator.
 5. SIMULATION (paper's real cell structure: repeat-group sizes and cell p):
    inject known extra-binomial variance between repeat groups, phi_true in
    {1, 1.25, 1.5, 2, 3}; recovery of the paper estimator vs an identifiable
    between-repeat Pearson estimator; rejection rate at alpha=0.05.
 6. REAL DATA with the identifiable estimator, paper cells and finer cells.
Writes A_PHI_RESULT_V1.json next to this script.
"""
from __future__ import annotations

import collections
import datetime as dt
import math
import re
import sys

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, __file__.rsplit("\\", 1)[0])
import audit_common as C  # noqa: E402

CELL_KEYS = ("model", "relation", "amount", "temperature", "condition", "mode",
             "hard", "task", "item", "persona", "json_format", "abstain_rule",
             "position", "answerable", "lines")
# The rows' own `cell` label ends in the repeat index ("... t=0.0 r3"), so it is
# used with that suffix stripped ("cell_norm"): the design cell the runner named.
FINE_EXTRA = ("experiment", "cell_norm", "cell_kind", "technique", "variant", "dose",
              "shots", "similarity", "depth", "derived_from", "form")
_RSUF = re.compile(r"\s*\br\d+\s*$")


def _get(r, k):
    if k == "cell_norm":
        c = r.get("cell")
        return None if c is None else _RSUF.sub("", str(c))
    return r.get(k)


def _has(r, k):
    return ("cell" in r) if k == "cell_norm" else (k in r)

PAPER_APPC = {  # Appendix C, verbatim numbers
    "mythos_battery_wave6_v1.jsonl": (40, 121.0, 1.01),
    "mythos_exploration_wave2_v1.jsonl": (76, 20.8, 1.04),
    "mythos_exploration_wave3_v1.jsonl": (52, 22.1, 1.05),
    "mythos_lepsilon_decisive_wave9_v1.jsonl": (12, 1302.8, 1.00),
    "mythos_reading_derived_wave11_v1.jsonl": (24, 141.7, 1.03),
    "mythos_technique_wave5_v1.jsonl": (8, 214.4, 1.01),
    "mythos_type_decomposition_wave10_v1.jsonl": (6, 603.2, 1.00),
}
PAPER_CEILING = "mythos_replication_wave4_v1.jsonl"
PAPER_MEDIAN = 1.01
FAR_FUTURE = dt.datetime.fromisoformat("2100-01-01T00:00:00")


def cells_of(rows, keys):
    cells = collections.defaultdict(list)
    for r in rows:
        if "repeat" not in r or r.get("verdict") in C.NON_EVENT:
            continue
        c = r.get("correct")
        if not isinstance(c, bool):
            continue
        key = tuple((k, _get(r, k)) for k in keys if _has(r, k))
        cells[key].append((r.get("repeat"), 1 if c else 0))
    return cells


def paper_phi(cells):
    """Exact re-implementation of mythos_noise_floor_v1.py main loop."""
    usable = {k: v for k, v in cells.items() if len(v) >= 4}
    if len(usable) < 5:
        return None
    chi2 = 0.0
    df = 0
    ns = []
    per_cell = []
    for v in usable.values():
        x = [b for _, b in v]
        n = len(x)
        ns.append(n)
        phat = sum(x) / n
        if phat in (0.0, 1.0):
            continue
        exp_var = phat * (1 - phat) / n
        obs = sum((xi - phat) ** 2 for xi in x) / (n - 1) / n
        chi2 += obs / exp_var
        df += 1
        per_cell.append((n, obs / exp_var))
    if df < 5:
        return {"cells": len(usable), "nbar": sum(ns) / len(ns), "phi": None,
                "per_cell": per_cell}
    return {"cells": len(usable), "nbar": sum(ns) / len(ns), "phi": chi2 / df,
            "per_cell": per_cell}


def group_phi(cells, min_n=4):
    """Identifiable estimator: Pearson X^2 of repeat-group counts against a
    common cell p (k x 2 heterogeneity chi-square), pooled over cells.
    Returns pooled X2, df, per-cell (X2, df, p)."""
    X2 = 0.0
    DF = 0
    per = []
    for key, v in cells.items():
        if len(v) < min_n:
            continue
        g = collections.defaultdict(lambda: [0, 0])
        for rep, b in v:
            g[rep][0] += b
            g[rep][1] += 1
        n = len(v)
        y = sum(b for _, b in v)
        p = y / n
        if p in (0.0, 1.0) or len(g) < 2:
            continue
        x2 = sum((yg - mg * p) ** 2 / (mg * p * (1 - p)) for yg, mg in g.values())
        d = len(g) - 1
        X2 += x2
        DF += d
        per.append((key, n, len(g), x2, d, float(stats.chi2.sf(x2, d))))
    return X2, DF, per


def load_wave(name, cutoff):
    return C.load(name, cutoff=cutoff)


def structure(cells):
    """Real structure for simulation: list of (group sizes, p) per cell."""
    out = []
    for v in cells.values():
        if len(v) < 4:
            continue
        g = collections.Counter(rep for rep, _ in v)
        p = sum(b for _, b in v) / len(v)
        if p in (0.0, 1.0):
            continue
        out.append((list(g.values()), p))
    return out


def simulate(struct, phi_true, rng):
    """Draw one synthetic wave with the real structure. Between-group extra
    variance: p_g ~ Beta with ICC rho_g = (phi-1)/(m_g-1), so that
    Var(y_g) = m_g p (1-p) phi for m_g > 1 (capped at phi <= m_g)."""
    cells = {}
    for ci, (ms, p) in enumerate(struct):
        v = []
        for gi, m in enumerate(ms):
            if phi_true > 1 and m > 1:
                rho = min((phi_true - 1) / (m - 1), 0.999)
                a = p * (1 - rho) / rho
                b = (1 - p) * (1 - rho) / rho
                pg = rng.beta(a, b)
            else:
                pg = p
            ys = rng.random(m) < pg
            v.extend((gi, int(t)) for t in ys)
        cells[ci] = v
    return cells


def main() -> int:
    res = {"id": "SUB70_AUDIT_A_PHI_V1", "source_dir": str(C.SRC),
           "cutoff": C.CUTOFF.isoformat(), "files": {}}
    names = list(PAPER_APPC) + [PAPER_CEILING, "mythos_steps_probe_v1.jsonl"]
    for nm in names:
        res["files"][nm] = C.sha256_file(C.SRC / nm)

    # 1. calibration --------------------------------------------------------
    print("### 1. reproduce Appendix C (paper estimator, frozen rows)")
    calib = {}
    ok_all = True
    frozen = {}
    for nm in names:
        rows = load_wave(nm, C.CUTOFF)
        frozen[nm] = rows
        cl = cells_of(rows, CELL_KEYS)
        r = paper_phi(cl)
        want = PAPER_APPC.get(nm)
        if r is None:
            got = None
        else:
            got = (r["cells"], round(r["nbar"], 1),
                   None if r["phi"] is None else round(r["phi"], 2))
        if want is not None:
            ok = got == want
        elif nm == PAPER_CEILING:
            ok = got is not None and got[2] is None  # all cells at ceiling/floor
        else:
            ok = True
        ok_all &= ok
        calib[nm] = {"paper": want, "recomputed": got, "match": ok}
        print("  %-44s paper %-22s recomputed %-22s %s" % (nm, want, got, "OK" if ok else "MISMATCH"))
    phis = sorted(v["recomputed"][2] for k, v in calib.items()
                  if k in PAPER_APPC and v["recomputed"])
    med = phis[len(phis) // 2]
    print("  median phi recomputed %.2f (paper %.2f); estimates contributing: %d"
          % (med, PAPER_MEDIAN, len(phis)))
    res["calibration"] = {"per_wave": calib, "median": med, "n_estimates": len(phis),
                          "all_match": ok_all and abs(med - PAPER_MEDIAN) < 0.005}

    # 2. known-bad ---------------------------------------------------------
    print("\n### 2. known-bad: cutoff removed -> must not reproduce Appendix C")
    bad_mismatch = 0
    kb = {}
    for nm, want in PAPER_APPC.items():
        r = paper_phi(cells_of(load_wave(nm, FAR_FUTURE), CELL_KEYS))
        got = (r["cells"], round(r["nbar"], 1), round(r["phi"], 2)) if r and r["phi"] else None
        kb[nm] = got
        if got != want:
            bad_mismatch += 1
        print("  %-44s %s %s" % (nm, got, "differs" if got != want else "same"))
    print("  waves that fail to reproduce without the cutoff: %d" % bad_mismatch)
    res["known_bad_no_cutoff"] = {"per_wave": kb, "n_mismatch": bad_mismatch}

    # 3. identity -----------------------------------------------------------
    print("\n### 3. identity: paper cell statistic vs n/(n-1)")
    maxdev = 0.0
    ncell = 0
    for nm in PAPER_APPC:
        r = paper_phi(cells_of(frozen[nm], CELL_KEYS))
        for n, s in r["per_cell"]:
            maxdev = max(maxdev, abs(s - n / (n - 1)))
            ncell += 1
    pred = {}
    for nm in PAPER_APPC:
        r = paper_phi(cells_of(frozen[nm], CELL_KEYS))
        pred[nm] = round(sum(n / (n - 1) for n, _ in r["per_cell"]) / len(r["per_cell"]), 4)
    print("  non-degenerate cells: %d, max |stat - n/(n-1)| = %.3e" % (ncell, maxdev))
    print("  phi predicted from cell sizes alone:", pred)
    res["identity"] = {"cells": ncell, "max_abs_dev": maxdev,
                       "phi_from_cell_sizes_only": pred,
                       "max_possible_cell_stat_at_n_ge_4": 4 / 3}

    # 4. injection on real cells -------------------------------------------
    print("\n### 4. injection: real cell structure, outcomes replaced by all-0/all-1 repeat blocks")
    inj = {}
    rng = np.random.default_rng(20260929)
    for nm in PAPER_APPC:
        cl = cells_of(frozen[nm], CELL_KEYS)
        new = {}
        for key, v in cl.items():
            reps = sorted({rep for rep, _ in v}, key=str)
            half = {rep: int(i % 2 == 0) for i, rep in enumerate(reps)}
            new[key] = [(rep, half[rep]) for rep, _ in v]
        pp = paper_phi(new)
        X2, DF, _ = group_phi(new)
        inj[nm] = {"paper_estimator": round(pp["phi"], 3) if pp and pp["phi"] else None,
                   "group_estimator": round(X2 / DF, 2) if DF else None}
        print("  %-44s paper-estimator %s   between-repeat estimator %s"
              % (nm, inj[nm]["paper_estimator"], inj[nm]["group_estimator"]))
    res["injection_extreme"] = inj

    # 5. simulation ---------------------------------------------------------
    print("\n### 5. simulation with the real structure of each wave (500 draws per phi)")
    PHIS = (1.0, 1.25, 1.5, 2.0, 3.0)
    NSIM = 500
    sim = {}
    for nm in PAPER_APPC:
        st = structure(cells_of(frozen[nm], CELL_KEYS))
        sim[nm] = {}
        for ph in PHIS:
            pe, ge, rej_g, rej_p = [], [], 0, 0
            for _ in range(NSIM):
                cl = simulate(st, ph, rng)
                pp = paper_phi(cl)
                if pp and pp["phi"] is not None:
                    pe.append(pp["phi"])
                    # paper decision rule: phi <= 1.15 read as "binomial"
                    rej_p += pp["phi"] > 1.15
                X2, DF, _ = group_phi(cl)
                if DF:
                    ge.append(X2 / DF)
                    rej_g += stats.chi2.sf(X2, DF) < 0.05
            sim[nm][str(ph)] = {
                "paper_mean": round(float(np.mean(pe)), 3),
                "paper_sd": round(float(np.std(pe)), 4),
                "paper_flag_rate_gt_1.15": round(rej_p / NSIM, 3),
                "group_mean": round(float(np.mean(ge)), 3),
                "group_sd": round(float(np.std(ge)), 3),
                "group_reject_rate_a05": round(rej_g / NSIM, 3)}
            s = sim[nm][str(ph)]
            print("  %-40s phi_true %.2f | paper %.3f (sd %.4f, flag %.2f) | between-repeat %.2f (sd %.2f, power %.2f)"
                  % (nm[:40], ph, s["paper_mean"], s["paper_sd"], s["paper_flag_rate_gt_1.15"],
                     s["group_mean"], s["group_sd"], s["group_reject_rate_a05"]))
    res["simulation"] = {"n_sim": NSIM, "phis": PHIS, "per_wave": sim,
                         "generator": "p_g ~ Beta(mean p_cell, ICC (phi-1)/(m_g-1)); real group sizes and cell p"}

    # 6. real data with identifiable estimator ------------------------------
    print("\n### 6. real data, between-repeat estimator (paper cells, then finer cells)")
    real = {}
    for label, keys in (("paper_cells", CELL_KEYS), ("fine_cells", CELL_KEYS + FINE_EXTRA)):
        real[label] = {}
        for nm in PAPER_APPC:
            X2, DF, per = group_phi(cells_of(frozen[nm], keys))
            if not DF:
                real[label][nm] = None
                continue
            flags01 = sum(1 for x in per if x[5] < 0.01)
            real[label][nm] = {"cells": len(per), "X2": round(X2, 1), "df": DF,
                               "phi_between_repeat": round(X2 / DF, 3),
                               "p_pooled": float(stats.chi2.sf(X2, DF)),
                               "cells_flagged_p_lt_0.01": flags01,
                               "expected_false_flags": round(0.01 * len(per), 2),
                               "worst_cells": [
                                   {"cell": dict(x[0]), "n": x[1], "groups": x[2],
                                    "X2": round(x[3], 1), "df": x[4], "p": x[5]}
                                   for x in sorted(per, key=lambda t: t[5])[:3]]}
            d = real[label][nm]
            print("  [%s] %-40s cells %3d  phi_b %.3f  df %4d  p %.3g  flagged(p<.01) %d (exp %.2f)"
                  % (label, nm[:40], d["cells"], d["phi_between_repeat"], DF, d["p_pooled"],
                     flags01, d["expected_false_flags"]))
    res["real_between_repeat"] = real

    # calibration of the identifiable estimator on real data ---------------
    print("\n### 6b. calibration of the between-repeat estimator on real cells")
    cal2 = {}
    for nm in PAPER_APPC:
        cl = cells_of(frozen[nm], CELL_KEYS)
        # known-null: permute outcomes across repeat groups within each cell
        vals = []
        rej = 0
        for _ in range(200):
            nul = {}
            for key, v in cl.items():
                b = [x for _, x in v]
                rng.shuffle(b)
                nul[key] = [(rep, bb) for (rep, _), bb in zip(v, b)]
            X2n, DFn, _ = group_phi(nul)
            vals.append(X2n / DFn)
            rej += stats.chi2.sf(X2n, DFn) < 0.05
        cal2[nm] = {"permuted_null_phi_mean": round(float(np.mean(vals)), 3),
                    "permuted_null_phi_2.5_97.5": [round(float(np.percentile(vals, 2.5)), 3),
                                                   round(float(np.percentile(vals, 97.5)), 3)],
                    "permuted_null_reject_rate_a05": rej / 200,
                    "injected_extreme_phi": inj[nm]["group_estimator"],
                    "observed_phi_paper_cells": real["paper_cells"][nm]["phi_between_repeat"]}
        print("  %-44s permuted-null mean %.3f [%.3f, %.3f] reject %.3f | injected %s | observed %s"
              % (nm, cal2[nm]["permuted_null_phi_mean"], *cal2[nm]["permuted_null_phi_2.5_97.5"],
                 cal2[nm]["permuted_null_reject_rate_a05"], cal2[nm]["injected_extreme_phi"],
                 cal2[nm]["observed_phi_paper_cells"]))
    res["between_repeat_calibration"] = cal2

    # 7. what a paper "cell" pools ------------------------------------------
    print("\n### 7. distinct runner-named design cells pooled inside one paper cell")
    pool = {}
    for nm in PAPER_APPC:
        per = collections.defaultdict(set)
        for r in frozen[nm]:
            if "repeat" not in r or r.get("verdict") in C.NON_EVENT or not isinstance(r.get("correct"), bool):
                continue
            key = tuple((k, r.get(k)) for k in CELL_KEYS if k in r)
            per[key].add(_get(r, "cell_norm"))
        sizes = [len(s) for s in per.values()]
        pool[nm] = {"paper_cells": len(per), "design_cells_per_paper_cell_min": min(sizes),
                    "design_cells_per_paper_cell_max": max(sizes),
                    "design_cells_per_paper_cell_mean": round(sum(sizes) / len(sizes), 1)}
        print("  %-44s %s" % (nm, pool[nm]))
    res["pooling"] = pool
    p = C.write_json("A_PHI_RESULT_V1.json", res)
    print("\nwrote", p)
    return 0 if res["calibration"]["all_match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
