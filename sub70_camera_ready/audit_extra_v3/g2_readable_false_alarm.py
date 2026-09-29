# -*- coding: utf-8 -*-
"""G2: measured flag rate of the paper's readable rule on repeats of the same design cell.

readable(n1, n2) = 2 * sqrt(phi * 0.25/n1 + phi * 0.25/n2), phi = 1.08 (Sec. 3). Threshold fixed before
this analysis; phi was estimated from these same repeats (Appendix C), which is a stated limit.

Two repeats of the same design cell are the same condition, so a pair the rule calls "readable" is a
false alarm. Reported separately, per Codex design note SUB70_G1_G3_EVIDENCE_DESIGN_REVIEW_V1:
  observed   - flag rate on real repeat pairs (all pairs; and one disjoint pair per cell, since pairs
               inside a cell share observations)
  null       - the same statistic after shuffling outcomes across the two repeats (known-null)
  known-bad  - one repeat's rate moved 0.5 away (clipped); the rule must fire on most such pairs
  by n       - broken down by the smaller repeat size, because the p = 0.5 bound is conservative
               away from 0.5 and the rule is coarse at small n
Cells: the seven Appendix C waves, repeats with >= 4 rows, cell pooled rate strictly inside (0, 1),
as the paper's phi estimate defines them. Frozen rows only, no model. Writes G2_READABLE_FALSE_ALARM_V1.json."""
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


def pairs_of(groups, disjoint):
    for key, g in groups.items():
        reps = sorted(g)
        it = zip(reps[0::2], reps[1::2]) if disjoint else itertools.combinations(reps, 2)
        for ra, rb in it:
            yield key, list(g[ra]), list(g[rb])


def fired(a, b):
    return abs(sum(a) / len(a) - sum(b) / len(b)) > readable(len(a), len(b))


def nbin(n):
    for lo, hi in NBINS:
        if lo <= n <= hi:
            return "%d-%s" % (lo, "" if hi > 10 ** 8 else hi)
    return "?"


def shift_half(a, b, rng):
    pa = sum(a) / len(a)
    target = pa + 0.5 if pa <= 0.5 else pa - 0.5
    k = round(target * len(b))
    b2 = [1] * k + [0] * (len(b) - k)
    rng.shuffle(b2)
    return a, b2


def permute(a, b, rng):
    pool = a + b
    rng.shuffle(pool)
    return pool[:len(a)], pool[len(a):]


class Tally:
    def __init__(self):
        self.f = defaultdict(int)
        self.t = defaultdict(int)

    def add(self, key, hit):
        self.f[key] += hit
        self.t[key] += 1

    def rate(self, key):
        return round(self.f[key] / self.t[key], 4) if self.t[key] else None

    def out(self):
        return {k: {"pairs": self.t[k], "fired": self.f[k], "rate": self.rate(k)} for k in sorted(self.t)}


def main():
    rng = random.Random(20260930)
    res = {"id": "SUB70_G2_READABLE_FALSE_ALARM_V1", "phi": PHI, "min_rows_per_repeat": MIN_GROUP, "nperm": NPERM,
           "rule": "readable(n1,n2) = 2*sqrt(phi*0.25/n1 + phi*0.25/n2)",
           "note": "phi 1.08 was estimated on these same repeats (Appendix C); pairs inside one cell share observations, "
                   "so the disjoint-pair figures are the independent ones", "per_wave": {}}
    obs_all, obs_dis, bad_all, null_all = Tally(), Tally(), Tally(), Tally()
    cells_any = defaultdict(lambda: [0, 0])
    for nm in PAPER_APPC:
        g = groups_of(cells_of(C.load(nm), CELL_KEYS + FINE_EXTRA))
        w = {"cells": len(g)}
        wa, wd, wb, wn = Tally(), Tally(), Tally(), Tally()
        for key, a, b in pairs_of(g, False):
            k = nbin(min(len(a), len(b)))
            h = fired(a, b)
            for t in (obs_all, wa):
                t.add("all", h); t.add(k, h)
            hb = fired(*shift_half(a, b, rng))
            for t in (bad_all, wb):
                t.add("all", hb); t.add(k, hb)
            for _ in range(NPERM):
                hn = fired(*permute(a, b, rng))
                for t in (null_all, wn):
                    t.add("all", hn); t.add(k, hn)
            cells_any[(nm, key)][0] |= h
            cells_any[(nm, key)][1] = 1
        for key, a, b in pairs_of(g, True):
            h = fired(a, b)
            obs_dis.add("all", h); obs_dis.add(nbin(min(len(a), len(b))), h); wd.add("all", h)
        w.update({"observed_all_pairs": wa.out(), "observed_disjoint_pairs": wd.out(),
                  "permuted_null": wn.out(), "known_bad_shift_0.5": wb.out()})
        res["per_wave"][nm] = w
        print("%-44s cells %3d pairs %5d obs %.3f | disjoint %4d obs %.3f | null %.3f | bad %.3f"
              % (nm, len(g), wa.t["all"], wa.rate("all") or 0, wd.t["all"], wd.rate("all") or 0,
                 wn.rate("all") or 0, wb.rate("all") or 0))
    nc = len(cells_any)
    res["pooled"] = {"cells": nc, "cells_with_any_flagged_pair": sum(v[0] for v in cells_any.values()),
                     "observed_all_pairs": obs_all.out(), "observed_disjoint_pairs": obs_dis.out(),
                     "permuted_null": null_all.out(), "known_bad_shift_0.5": bad_all.out(),
                     "reference_only_nominal_two_se_at_p_half": 0.0455}
    print("pooled: cells %d (any flagged %d) | all pairs %d obs %.4f | disjoint %d obs %.4f | null %.4f | bad %.4f"
          % (nc, res["pooled"]["cells_with_any_flagged_pair"], obs_all.t["all"], obs_all.rate("all"),
             obs_dis.t["all"], obs_dis.rate("all"), null_all.rate("all"), bad_all.rate("all")))
    for k in sorted(obs_all.t):
        if k != "all":
            print("  n-bin %-8s pairs %5d obs %.3f null %.3f bad %.3f"
                  % (k, obs_all.t[k], obs_all.rate(k), null_all.rate(k), bad_all.rate(k)))
    res["inputs"] = {nm: C.sha256_file(C.SRC / nm)[:12] for nm in PAPER_APPC}
    (HERE / "G2_READABLE_FALSE_ALARM_V1.json").write_text(json.dumps(res, indent=1), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
