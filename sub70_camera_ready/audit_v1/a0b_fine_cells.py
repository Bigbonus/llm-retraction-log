# -*- coding: utf-8 -*-
"""Exploration only: size and degeneracy of finer cells (paper keys plus the
condition columns the paper's key omits)."""
import collections
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, __file__.rsplit("\\", 1)[0])
import audit_common as C  # noqa: E402
from a1_phi_identifiability import CELL_KEYS, FINE_EXTRA, PAPER_APPC, cells_of  # noqa: E402

for nm in PAPER_APPC:
    rows = C.load(nm)
    for extra in (("experiment",), ("cell",), FINE_EXTRA):
        cl = cells_of(rows, CELL_KEYS + tuple(extra))
        sizes = collections.Counter(len(v) for v in cl.values())
        nondeg = sum(1 for v in cl.values() if len(v) >= 4 and 0 < sum(b for _, b in v) < len(v))
        print("%-42s +%-10s cells %4d  nondegenerate>=4 %4d  sizes %s"
              % (nm[:42], extra[0] if len(extra) == 1 else "all", len(cl), nondeg,
                 sizes.most_common(4)))
