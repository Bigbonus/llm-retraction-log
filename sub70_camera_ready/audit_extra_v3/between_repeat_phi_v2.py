# -*- coding: utf-8 -*-
"""Between-repeat over-dispersion (phi) from any evaluation log, no schema assumed. Standard library only.
V2: malformed input is refused, not dropped (Codex review SUB70_G1_G2_INTERPRETATION_REVIEW_V1, item 3).

Input: a CSV with a header and three columns, in any order, named
    cell     - the design cell (model x condition x ...), non-blank string
    repeat   - the repeat index within that cell, non-blank string
    correct  - one of 1/0, true/false, t/f, yes/no, y/n (case-insensitive)
Any other column is ignored. Non-events (errors, truncations) must not be rows here; exclude them
before writing the CSV and say how many you excluded. This file cannot check that for you.

Refusals (exit 2, with row numbers): a blank cell or repeat, a `correct` value outside the set
above, a missing column. Nothing is silently dropped, so the denominators are exactly the rows given.

For each cell with >= MIN_N rows, >= 2 repeats and a pooled rate strictly between 0 and 1, the Pearson
X^2 of the per-repeat counts against the pooled rate is summed; phi = sum X^2 / sum df, df = repeats - 1.
Cells that fail those conditions are counted and reported, not hidden.

What the three-column format cannot verify: whether repeats re-used the same items, whether outcomes
are exchangeable across repeats, or whether two cells are really the same condition. phi is a
between-repeat statistic under those assumptions, and the reader owns them.

Usage:
    python between_repeat_phi_v2.py cells.csv     # phi, df, cells used and excluded, permutation p
    python between_repeat_phi_v2.py --selftest    # smoke test on one binomial and one injected fixture

The self-test is a smoke test with one seed: it shows the estimator reads ~1 on binomial repeats and
well above 1 on injected between-repeat variance. It is not an estimate of any error rate.
"""
import csv
import random
import sys
from collections import defaultdict

MIN_N = 4
NPERM = 1000
TRUE = {"1", "true", "t", "yes", "y"}
FALSE = {"0", "false", "f", "no", "n"}


class BadInput(Exception):
    pass


def read_cells(path):
    cells = defaultdict(list)
    problems = []
    with open(path, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        names = {h.strip().lower(): h for h in (rd.fieldnames or [])}
        missing = {"cell", "repeat", "correct"} - set(names)
        if missing:
            raise BadInput("missing column(s): %s (found %s)" % (sorted(missing), rd.fieldnames))
        for i, row in enumerate(rd, start=2):  # header is line 1
            cell = (row.get(names["cell"]) or "").strip()
            rep = (row.get(names["repeat"]) or "").strip()
            v = (row.get(names["correct"]) or "").strip().lower()
            if not cell or not rep:
                problems.append("line %d: blank cell or repeat" % i)
            elif v not in TRUE and v not in FALSE:
                problems.append("line %d: correct=%r is not 1/0, true/false, yes/no" % (i, row.get(names["correct"])))
            else:
                cells[cell].append((rep, 1 if v in TRUE else 0))
            if len(problems) >= 20:
                problems.append("... stopping after 20 problems")
                break
    if problems:
        raise BadInput("refused, no number computed:\n  " + "\n  ".join(problems))
    return cells


def split_usable(cells):
    used, why = {}, defaultdict(int)
    for k, v in cells.items():
        y = sum(b for _, b in v)
        if len(v) < MIN_N:
            why["fewer than %d rows" % MIN_N] += 1
        elif y == 0 or y == len(v):
            why["rate 0 or 1"] += 1
        elif len({r for r, _ in v}) < 2:
            why["single repeat"] += 1
        else:
            used[k] = v
    return used, dict(why)


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
    """Shuffle outcomes across repeats inside each cell. Valid as a null only if outcomes are
    exchangeable across repeats, which this file cannot check."""
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
    used, why = split_usable(cells)
    rows_in = sum(len(v) for v in cells.values())
    rows_used = sum(len(v) for v in used.values())
    print("rows given %d, rows in usable cells %d, cells given %d, cells used %d, excluded %s"
          % (rows_in, rows_used, len(cells), len(used), why or "none"))
    if not used:
        print("no usable cell")
        return None
    X2, DF = phi(used)
    p, null_mean = permutation_p(used, X2, rng)
    print("cells used %d  df %d  phi %.3f  permutation p %.3f  (null mean %.3f)" % (len(used), DF, X2 / DF, p, null_mean))
    return X2 / DF, DF, p


def _simulate(rng, ncell=60, nrep=4, m=12, phi_true=1.0):
    """Repeat groups of size m; group rate Beta-binomial around p with the given phi (1.0 = binomial)."""
    cells = defaultdict(list)
    for c in range(ncell):
        p = rng.uniform(0.2, 0.8)
        for r in range(nrep):
            if phi_true > 1.0:
                rho = (phi_true - 1) / (m - 1)
                s = (1 - rho) / rho
                pr = rng.betavariate(p * s, (1 - p) * s)
            else:
                pr = p
            cells["c%d" % c].extend((str(r), 1 if rng.random() < pr else 0) for _ in range(m))
    return cells


def selftest():
    rng = random.Random(20260930)
    print("smoke test, one seed. known-good: binomial repeats, expect phi ~ 1 and p not small")
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
    try:
        cells = read_cells(sys.argv[1])
    except BadInput as e:
        print(e, file=sys.stderr)
        sys.exit(2)
    sys.exit(0 if report(cells, random.Random(0)) else 1)
