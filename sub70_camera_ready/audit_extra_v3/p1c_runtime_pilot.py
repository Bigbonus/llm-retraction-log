# -*- coding: utf-8 -*-
"""P1-c runtime pilot. Times one dataset per (C, m) for the S1 generator and the phi test with
NPERM = 1000. Prints seconds only. It does not print phi, p, or any rejection outcome, so nothing
about effects can be read from this run (Codex: benchmark runtime only)."""
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import between_repeat_phi_v3 as M  # noqa: E402

R = 4
NPERM = 1000


def s1(rng, C, m):
    cells = defaultdict(list)
    for c in range(C):
        p = rng.uniform(0.2, 0.8)
        for r in range(R):
            cells["c%d" % c].extend((str(r), 1 if rng.random() < p else 0) for _ in range(m))
    return cells


rows = []
for C in (20, 60, 166):
    for m in (4, 8, 12):
        rng = random.Random(1)
        t0 = time.perf_counter()
        cells = s1(rng, C, m)
        t1 = time.perf_counter()
        used, _ = M.split_usable(cells)
        X2, DF = M.phi(used)
        M.permutation_p(used, X2, rng, nperm=NPERM)
        t2 = time.perf_counter()
        rows.append((C, m, t1 - t0, t2 - t1))
        print("C %3d  m %2d  generate %.3fs  phi+%d perms %.2fs" % (C, m, t1 - t0, NPERM, t2 - t1))
tot = sum(r[3] for r in rows)
print("sum over the 9 (C,m) points, one dataset each: %.1fs" % tot)
print("proposed grid 45 points x 200 datasets at these costs: about %.0f min on one core" % (tot * 5 * 200 / 60))
