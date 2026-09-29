# -*- coding: utf-8 -*-
"""Between-repeat over-dispersion (phi) from any evaluation log, no schema assumed. Standard library only.

Input: a CSV with a header and three columns, in any order, named
    cell     - the design cell (model x condition x ...), any string
    repeat   - the repeat index within that cell, any string
    correct  - 1/0, true/false, yes/no
Everything else in the file is ignored. Non-events (errors, truncations) should not be rows here.

For each cell with >= MIN_N rows, >= 2 repeats and a pooled rate strictly between 0 and 1, the Pearson
X^2 of the per-repeat counts against the pooled rate is summed; phi = sum X^2 / sum df, df = repeats - 1.
phi ~ 1 means repeats are no more variable than binomial; phi >> 1 means something between repeats moved.

Usage:
    python between_repeat_phi.py cells.csv            # prints phi, df, cells used, and a permutation p
    python between_repeat_phi.py --selftest           # known-good (binomial) and known-bad (injected) checks

The self-test is the calibration: the estimator must read ~1 on binomial data and >> 1 on injected
between-repeat variance, or it is not measuring anything. Run it before trusting a number.
"""
import csv
import random
import sys
from collections import defaultdict

MIN_N = 4
NPERM = 1000
TRUE = {"1", "true", "t", "yes", "y"}
FALSE = {"0", "false", "f", "no", "n"}


def read_cells(path):
    cells = defaultdict(list)
    with open(path, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        need = {"cell", "repeat", "correct"}
        if not need <= set(h.strip().lower() for h in rd.fieldnames or []):
            sys.exit("need columns: cell, repeat, correct (found: %s)" % rd.fieldnames)
        for row in rd:
            row = {k.strip().lower(): v for k, v in row.items()}
            v = str(row["correct"]).strip().lower()
            if v in TRUE:
                b = 1
            elif v in FALSE:
                b = 0
            else:
                continue
            cells[row["cell"]].append((row["repeat"], b))
    return cells


def usable(cells):
    out = {}
    for k, v in cells.items():
        if len(v) < MIN_N:
            continue
        y = sum(b for _, b in v)
        if y == 0 or y == len(v) or len({r for r, _ in v}) < 2:
            continue
        out[k] = v
    return out


def phi(cells):
    X2 = 0.0
    DF = 0
    for v in cells.values():
        g = defaultdict(lambda: [0, 0])
        for rep, b in v:
            g[rep][0] += b
            g[rep][1] += 1
        p = sum(b for _, b in v) / len(v)
        X2 += sum((yg - mg * p) ** 2 / (mg * p * (1 - p)) for yg, mg in g.values())
        DF += len(g) - 1
    return X2, DF


def permutation_p(cells, x2_obs, rng, nperm=NPERM):
    """Shuffle outcomes across repeats inside each cell (keeps every cell's rate and group sizes)."""
    hits = 0
    nulls = []
    for _ in range(nperm):
        nul = {}
        for k, v in cells.items():
            b = [x for _, x in v]
            rng.shuffle(b)
            nul[k] = [(rep, bb) for (rep, _), bb in zip(v, b)]
        x2, df = phi(nul)
        nulls.append(x2 / df)
        hits += x2 >= x2_obs
    return (1 + hits) / (nperm + 1), sum(nulls) / len(nulls)


def report(cells, rng):
    u = usable(cells)
    if not u:
        print("no usable cell (need >= %d rows, >= 2 repeats, rate strictly between 0 and 1)" % MIN_N)
        return None
    X2, DF = phi(u)
    p, null_mean = permutation_p(u, X2, rng)
    print("cells used %d  df %d  phi %.3f  permutation p %.3f  (null mean %.3f)" % (len(u), DF, X2 / DF, p, null_mean))
    return X2 / DF, DF, p


def _simulate(rng, ncell=60, nrep=4, m=12, phi_true=1.0):
    """Repeat groups of size m; the group rate is Beta-binomial around p with the given phi (1.0 = binomial)."""
    cells = defaultdict(list)
    for c in range(ncell):
        p = rng.uniform(0.2, 0.8)
        for r in range(nrep):
            if phi_true > 1.0:
                # Beta-binomial: over-dispersion phi = 1 + (m - 1) rho, rho = 1 / (a + b + 1)
                rho = (phi_true - 1) / (m - 1)
                s = (1 - rho) / rho
                pr = rng.betavariate(p * s, (1 - p) * s)
            else:
                pr = p
            cells["c%d" % c].extend((str(r), 1 if rng.random() < pr else 0) for _ in range(m))
    return cells


def selftest():
    rng = random.Random(20260930)
    print("known-good: binomial repeats, 60 cells x 4 repeats x 12 rows, expect phi ~ 1 and p not small")
    good = report(_simulate(rng), rng)
    print("known-bad: injected between-repeat variance phi_true = 2.0, expect phi >> 1 and p small")
    bad = report(_simulate(rng, phi_true=2.0), rng)
    ok = good is not None and bad is not None and 0.8 <= good[0] <= 1.25 and bad[0] >= 1.5 and bad[2] < 0.01
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(0 if report(read_cells(sys.argv[1]), random.Random(0)) else 1)
