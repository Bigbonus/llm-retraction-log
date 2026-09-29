# -*- coding: utf-8 -*-
"""Exploration only: why does group_phi return nothing on fine cells?"""
import collections
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, __file__.rsplit("\\", 1)[0])
import audit_common as C  # noqa: E402
from a1_phi_identifiability import CELL_KEYS, FINE_EXTRA, cells_of, group_phi  # noqa: E402

rows = C.load("mythos_battery_wave6_v1.jsonl")
cl = cells_of(rows, CELL_KEYS + FINE_EXTRA)
nd = [(k, v) for k, v in cl.items() if len(v) >= 4 and 0 < sum(b for _, b in v) < len(v)]
k, v = nd[0]
print(dict(k))
print(v)
print(collections.Counter(rep for rep, _ in v))
print(group_phi(dict(nd[:5]))[:2])
