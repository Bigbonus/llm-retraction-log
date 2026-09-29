# -*- coding: utf-8 -*-
"""Exploration only: how are the paper's phi cells structured?
For each wave that carries a `repeat` column, count rows per (cell, repeat)
and list which other columns vary inside a cell."""
from __future__ import annotations

import collections
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, __file__.rsplit("\\", 1)[0])
from audit_common import NON_EVENT, load, wave_files  # noqa: E402

CELL_KEYS = ("model", "relation", "amount", "temperature", "condition", "mode",
             "hard", "task", "item", "persona", "json_format", "abstain_rule",
             "position", "answerable", "lines")

for p in wave_files():
    rows = load(p.name)
    rows = [r for r in rows if "repeat" in r and r.get("verdict") not in NON_EVENT
            and isinstance(r.get("correct"), bool)]
    if not rows:
        continue
    cells = collections.defaultdict(list)
    for r in rows:
        key = tuple((k, r.get(k)) for k in CELL_KEYS if k in r)
        cells[key].append(r)
    usable = {k: v for k, v in cells.items() if len(v) >= 4}
    per_rep = collections.Counter()
    reps_per_cell = []
    varying = collections.Counter()
    for k, v in usable.items():
        g = collections.Counter(r.get("repeat") for r in v)
        reps_per_cell.append(len(g))
        for c in g.values():
            per_rep[c] += 1
        for col in ("seed", "ts", "runner_version", "prompt", "item_id", "truth"):
            vals = {str(r.get(col))[:13] for r in v}
            if len(vals) > 1:
                varying[col] += 1
    if not usable:
        continue
    print(p.name, "cells>=4:", len(usable), "keys:", [k for k, _ in next(iter(usable))])
    print("   rows per (cell,repeat) histogram (top):", per_rep.most_common(6))
    print("   distinct repeats per cell (min/max):", min(reps_per_cell), max(reps_per_cell))
    print("   columns varying within cell (#cells):", dict(varying))
    print("   extra columns in a row:", sorted(set(rows[0]) - set(CELL_KEYS))[:40])
