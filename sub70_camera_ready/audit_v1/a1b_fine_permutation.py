# -*- coding: utf-8 -*-
"""Objection A, part 2: permutation p-values for the between-repeat
estimator on design cells (paper key + runner-named design cell), so the
chi-square approximation on sparse cells is not trusted blindly.
Also: do repeats re-use the same items? (only where rows carry `truth`).
Writes A_PHI_FINE_PERMUTATION_V1.json."""
from __future__ import annotations

import collections
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, __file__.rsplit("\\", 1)[0])
import audit_common as C  # noqa: E402
from a1_phi_identifiability import (CELL_KEYS, FINE_EXTRA, PAPER_APPC, _get,  # noqa: E402
                                    cells_of, group_phi)

NPERM = 1000
rng = np.random.default_rng(20260929)
res = {"id": "SUB70_AUDIT_A_PHI_FINE_PERM_V1", "nperm": NPERM, "per_wave": {}}
allX2 = 0.0
allDF = 0
null_tot = np.zeros(NPERM)
for nm in PAPER_APPC:
    rows = C.load(nm)
    cl = cells_of(rows, CELL_KEYS + FINE_EXTRA)
    X2, DF, per = group_phi(cl)
    keep = {k: v for k, v in cl.items()
            if len(v) >= 4 and 0 < sum(b for _, b in v) < len(v)
            and len({rep for rep, _ in v}) >= 2}
    nulls = np.zeros(NPERM)
    for i in range(NPERM):
        nul = {}
        for key, v in keep.items():
            b = [x for _, x in v]
            rng.shuffle(b)
            nul[key] = [(rep, bb) for (rep, _), bb in zip(v, b)]
        nulls[i] = group_phi(nul)[0]
    p_perm = float((1 + np.sum(nulls >= X2)) / (NPERM + 1))
    allX2 += X2
    allDF += DF
    null_tot += nulls
    # item re-use across repeats (only rows that log truth)
    reuse = None
    tr = [r for r in rows if "truth" in r and "repeat" in r]
    if tr:
        by = collections.defaultdict(lambda: collections.defaultdict(set))
        for r in tr:
            dk = (r.get("model"), r.get("temperature"), _get(r, "cell_norm"))
            by[dk][r.get("repeat")].add(str(r.get("truth")))
        same = diff = 0
        for dk, reps in by.items():
            sets = list(reps.values())
            if len(sets) < 2:
                continue
            if all(s == sets[0] for s in sets):
                same += 1
            else:
                diff += 1
        reuse = {"design_cells_same_truth_set_every_repeat": same,
                 "design_cells_truth_set_differs_between_repeats": diff}
    res["per_wave"][nm] = {"cells": len(per), "phi_between_repeat": round(X2 / DF, 3), "df": DF,
                           "X2": round(X2, 1), "p_permutation": p_perm,
                           "null_phi_mean": round(float(np.mean(nulls)) / DF, 3),
                           "item_reuse": reuse}
    print("%-44s cells %3d phi_b %.3f  perm p %.4f  null-mean %.3f  reuse %s"
          % (nm, len(per), X2 / DF, p_perm, np.mean(nulls) / DF, reuse))
p_all = float((1 + np.sum(null_tot >= allX2)) / (NPERM + 1))
res["pooled"] = {"phi_between_repeat": round(allX2 / allDF, 3), "df": allDF,
                 "p_permutation": p_all,
                 "null_phi_mean": round(float(np.mean(null_tot)) / allDF, 3)}
print("pooled 7 waves: phi_b %.3f df %d perm p %.4f null-mean %.3f"
      % (allX2 / allDF, allDF, p_all, np.mean(null_tot) / allDF))
print("wrote", C.write_json("A_PHI_FINE_PERMUTATION_V1.json", res))
