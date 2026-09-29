# -*- coding: utf-8 -*-
"""G1 check: export the paper's design cells (same 7 waves, same keys as the audit's fine cells) from the
frozen logs to the schema-free CSV, run between_repeat_phi.py on it, and compare with the published
pooled value (Appendix C: phi 1.076, df 1,424, 166 cells). If the schema-free script does not reproduce
the audit's number on the audit's own cells, it is not the same estimator."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUD = Path(r"G:\chappy_ai_storage\handoff\judge2026_submit_camera_ready_audit_v1")
sys.path.insert(0, str(AUD))
import audit_common as C  # noqa: E402
from a1_phi_identifiability import CELL_KEYS, FINE_EXTRA, PAPER_APPC, cells_of  # noqa: E402

PUBLISHED = {"phi": 1.076, "df": 1424, "cells": 166}

out = HERE / "G1_design_cells.csv"
n = 0
with open(out, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["cell", "repeat", "correct"])
    for nm in PAPER_APPC:
        for key, v in cells_of(C.load(nm), CELL_KEYS + FINE_EXTRA).items():
            cell = nm + "|" + "|".join("%s=%s" % kv for kv in key)
            for rep, b in v:
                w.writerow([cell, rep, b])
                n += 1
print("rows exported", n, "->", out.name)

p = subprocess.run([sys.executable, str(HERE / "between_repeat_phi.py"), str(out)], capture_output=True, text=True)
print(p.stdout.strip())
line = p.stdout.strip().splitlines()[-1].split()
got = {"cells": int(line[2]), "df": int(line[4]), "phi": float(line[6])}
match = got["cells"] == PUBLISHED["cells"] and got["df"] == PUBLISHED["df"] and abs(got["phi"] - PUBLISHED["phi"]) < 0.0015
print("reproduces Appendix C pooled:", match, got)
(HERE / "G1_REPRODUCTION_V1.json").write_text(json.dumps(
    {"id": "SUB70_G1_SCHEMA_FREE_REPRODUCTION_V1", "rows": n, "published": PUBLISHED, "got": got,
     "match": match, "sha256_between_repeat_phi": C.sha256_file(HERE / "between_repeat_phi.py")[:12]},
    indent=1), encoding="utf-8", newline="\n")
sys.exit(0 if match else 1)
