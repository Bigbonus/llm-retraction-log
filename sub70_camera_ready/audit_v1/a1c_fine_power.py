# -*- coding: utf-8 -*-
"""Objection A, part 3: power of the between-repeat estimator on the real
design-cell structure (7 waves pooled), for known phi_true.
Writes A_PHI_FINE_POWER_V1.json."""
from __future__ import annotations

import sys

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, __file__.rsplit("\\", 1)[0])
import audit_common as C  # noqa: E402
from a1_phi_identifiability import (CELL_KEYS, FINE_EXTRA, PAPER_APPC, cells_of,  # noqa: E402
                                    group_phi, paper_phi, simulate, structure)

rng = np.random.default_rng(20260930)
struct = []
for nm in PAPER_APPC:
    struct += structure(cells_of(C.load(nm), CELL_KEYS + FINE_EXTRA))
struct = [s for s in struct if len(s[0]) >= 2]
NSIM = 300
ALL = {}
out = {"id": "SUB70_AUDIT_A_PHI_FINE_POWER_V1", "cells": len(struct), "nsim": NSIM, "rows": {}}
print("design cells in pooled structure:", len(struct))
for ph in (1.0, 1.1, 1.25, 1.5, 2.0):
    est, rej, pe = [], 0, []
    for _ in range(NSIM):
        cl = simulate(struct, ph, rng)
        X2, DF, _ = group_phi(cl)
        est.append(X2 / DF)
        rej += stats.chi2.sf(X2, DF) < 0.05
        pp = paper_phi(cl)
        pe.append(pp["phi"])
    ALL[ph] = est
    out["rows"][str(ph)] = {"between_mean": round(float(np.mean(est)), 3),
                            "between_sd": round(float(np.std(est)), 3),
                            "reject_rate_chi2_a05": round(float(rej) / NSIM, 3),
                            "paper_estimator_mean": round(float(np.mean(pe)), 4)}
    print(ph, out["rows"][str(ph)])
thr = float(np.percentile(ALL[1.0], 95))
out["null_calibrated_threshold_95pct"] = round(thr, 4)
for ph, e in ALL.items():
    out["rows"][str(ph)]["power_null_calibrated_a05"] = round(float(np.mean(np.array(e) > thr)), 3)
    print("null-calibrated power", ph, out["rows"][str(ph)]["power_null_calibrated_a05"])
print("threshold", thr)
print("wrote", C.write_json("A_PHI_FINE_POWER_V1.json", out))
