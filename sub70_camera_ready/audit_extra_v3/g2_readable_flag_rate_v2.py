# -*- coding: utf-8 -*-
"""G2 V2: flag rate of the paper's readable rule on repeats of the same design cell, with the
interpretation corrected per Codex review SUB70_G1_G2_INTERPRETATION_REVIEW_V1.

readable(n1, n2) = 2 sqrt(1.08 (0.25/n1 + 0.25/n2)) (Sec. 3). Threshold fixed before this analysis.

Three things are measured and kept apart:
  A. within-condition flag rate: how often the rule fires on two repeats that carry the same design
     label. Equal labels do not prove equal outcome distributions, so this is NOT an established
     false-positive rate. Shuffled-outcome rate is reported next to it; it is a null only under
     exchangeability of individual outcomes across repeats, which these logs cannot establish
     (item re-use across repeats is not logged in every wave).
  B. fixture: the second repeat's count is set to round((p1 +/- 0.5) n2). This is a deterministic
     perturbation, not a sample from a population, so its flag rate is a fixture result, not power.
     The realized |difference| after rounding is reported with it.
  C. Monte Carlo power, preregistered here before running: for each real pair size (n1, n2), draw both
     arms from Binomial with (p1, p2) in {(0.25, 0.75), (0.40, 0.90), (0.50, 0.80)}, 400 draws per
     pair, and report the fraction flagged with its Monte Carlo standard error. This is the only
     "power" figure, and it is for those population pairs at these sizes, nothing else.
Pairs inside one cell share observations; pairs across cells share items and waves. No figure here
is an independent-sample estimate. Cells: seven Appendix C waves, repeats with >= 4 rows, cell
pooled rate strictly inside (0, 1). Frozen rows only, no model. Writes G2_READABLE_FLAG_RATE_V2.json."""
from __future__ import annotations

import itertools
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUD = Path(r"G:\chappy_ai_storage\handoff\judge2026_submit_camera_ready_audit_v1")
sys.path.insert(0, str(AUD))
import audit_common as C  # noqa: E402
from a1_phi_identifiability import CELL_KEYS, FINE_EXTRA, PAPER_APPC, cells_of  # noqa: E402

PHI = 1.08
MIN_GROUP = 4
NPERM = 200
NDRAW = 400
POWER_PAIRS = ((0.25, 0.75), (0.40, 0.90), (0.50, 0.80))
NBINS = ((4, 7), (8, 15), (16, 31), (32, 10 ** 9))


def readable(n1, n2, phi=PHI):
    return 2 * math.sqrt(phi * 0.25 / n1 + phi * 0.25 / n2)


def groups_of(cells):
    out = {}
    for key, v in cells.items():
        y = sum(b for _, b in v)
        if y == 0 or y == len(v):
            continue
        g = defaultdict(list)
        for rep, b in v:
            g[rep].append(b)
        g = {r: x for r, x in g.items() if len(x) >= MIN_GROUP}
        if len(g) >= 2:
            out[key] = g
    return out


def nbin(n):
    for lo, hi in NBINS:
        if lo <= n <= hi:
            return "%d-%s" % (lo, "" if hi > 10 ** 8 else hi)
    return "?"


def fires(a, b):
    return abs(sum(a) / len(a) - sum(b) / len(b)) > readable(len(a), len(b))


class Tally:
    def __init__(self):
        self.f, self.t, self.x = defaultdict(int), defaultdict(int), defaultdict(float)

    def add(self, key, hit, extra=0.0):
        self.f[key] += hit
        self.t[key] += 1
        self.x[key] += extra

    def out(self, extra_name=None):
        o = {}
        for k in sorted(self.t):
            d = {"pairs": self.t[k], "fired": self.f[k], "rate": round(self.f[k] / self.t[k], 4)}
            if extra_name:
                d[extra_name] = round(self.x[k] / self.t[k], 4)
            o[k] = d
        return o


def main():
    rng = random.Random(20260930)
    res = {"id": "SUB70_G2_READABLE_FLAG_RATE_V2", "supersedes": "SUB70_G2_READABLE_FALSE_ALARM_V1",
           "phi": PHI, "min_rows_per_repeat": MIN_GROUP, "nperm": NPERM, "ndraw": NDRAW,
           "power_pairs_preregistered": POWER_PAIRS,
           "rule": "readable(n1,n2) = 2*sqrt(phi*0.25/n1 + phi*0.25/n2)",
           "assumptions": ["phi 1.08 was estimated on these same repeats",
                           "A is a within-condition flag rate, not an established false-positive rate",
                           "shuffled rate is a null only under exchangeability across repeats, not established",
                           "B is a deterministic fixture, not power",
                           "no figure is an independent-sample estimate: pairs share rows, items, cells, waves"],
           "per_wave": {}}
    A, A_shuf, B, Cp = Tally(), Tally(), Tally(), {pp: Tally() for pp in POWER_PAIRS}
    for nm in PAPER_APPC:
        g = groups_of(cells_of(C.load(nm), CELL_KEYS + FINE_EXTRA))
        wa, ws, wb = Tally(), Tally(), Tally()
        for key, gr in g.items():
            for ra, rb in itertools.combinations(sorted(gr), 2):
                a, b = list(gr[ra]), list(gr[rb])
                k = nbin(min(len(a), len(b)))
                h = fires(a, b)
                for t in (A, wa):
                    t.add("all", h); t.add(k, h)
                for _ in range(NPERM):
                    pool = a + b
                    rng.shuffle(pool)
                    hs = fires(pool[:len(a)], pool[len(a):])
                    for t in (A_shuf, ws):
                        t.add("all", hs); t.add(k, hs)
                # B: deterministic fixture
                pa = sum(a) / len(a)
                target = pa + 0.5 if pa <= 0.5 else pa - 0.5
                kk = round(target * len(b))
                b2 = [1] * kk + [0] * (len(b) - kk)
                realized = abs(kk / len(b) - pa)
                hb = fires(a, b2)
                for t in (B, wb):
                    t.add("all", hb, realized); t.add(k, hb, realized)
                # C: Monte Carlo power at these sizes
                for pp in POWER_PAIRS:
                    p1, p2 = pp
                    n1, n2 = len(a), len(b)
                    thr = readable(n1, n2)
                    for _ in range(NDRAW):
                        y1 = sum(rng.random() < p1 for _ in range(n1))
                        y2 = sum(rng.random() < p2 for _ in range(n2))
                        hc = abs(y1 / n1 - y2 / n2) > thr
                        Cp[pp].add("all", hc); Cp[pp].add(k, hc)
        res["per_wave"][nm] = {"cells": len(g), "A_within_condition": wa.out(),
                               "A_shuffled": ws.out(), "B_fixture": wb.out("mean_realized_abs_diff")}
        print("%-44s cells %3d pairs %5d  A %.3f  shuffled %.3f  B %.3f (realized %.2f)"
              % (nm, len(g), wa.t["all"], (wa.f["all"] / wa.t["all"]) if wa.t["all"] else 0,
                 (ws.f["all"] / ws.t["all"]) if ws.t["all"] else 0,
                 (wb.f["all"] / wb.t["all"]) if wb.t["all"] else 0,
                 (wb.x["all"] / wb.t["all"]) if wb.t["all"] else 0))
    power = {}
    for pp, t in Cp.items():
        power["p1=%.2f,p2=%.2f" % pp] = {k: {"draws": t.t[k], "power": round(t.f[k] / t.t[k], 4),
                                             "mc_se": round(math.sqrt((t.f[k] / t.t[k]) * (1 - t.f[k] / t.t[k]) / t.t[k]), 4)}
                                         for k in sorted(t.t)}
    res["pooled"] = {"A_within_condition": A.out(), "A_shuffled": A_shuf.out(),
                     "B_fixture": B.out("mean_realized_abs_diff"), "C_power_monte_carlo": power}
    print("pooled A %.4f (pairs %d)  shuffled %.4f  B %.4f realized %.3f"
          % (A.f["all"] / A.t["all"], A.t["all"], A_shuf.f["all"] / A_shuf.t["all"],
             B.f["all"] / B.t["all"], B.x["all"] / B.t["all"]))
    for k in sorted(A.t):
        print("  n-bin %-6s pairs %5d  A %.3f  shuffled %.3f  B %.3f (realized %.2f)  power %s"
              % (k, A.t[k], A.f[k] / A.t[k], A_shuf.f[k] / A_shuf.t[k], B.f[k] / B.t[k], B.x[k] / B.t[k],
                 " ".join("%s:%.2f" % (pp, power[pp][k]["power"]) for pp in power)))
    res["inputs"] = {nm: C.sha256_file(C.SRC / nm)[:12] for nm in PAPER_APPC}
    (HERE / "G2_READABLE_FLAG_RATE_V2.json").write_text(json.dumps(res, indent=1), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
