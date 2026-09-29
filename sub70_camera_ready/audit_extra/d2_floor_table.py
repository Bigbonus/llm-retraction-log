# -*- coding: utf-8 -*-
"""Readable-difference table and calibration rows at the corrected phi.
CALIBRATE: at phi = 1.01 reproduce the paper's table (0.82 ... 0.12) and the
three calibration rows (thresholds 0.58, 0.71, 0.07; case E n=384, diff 0.56).
KNOWN-BAD: the formula without the factor 2 must fail the table check.
Then the same at phi from A_PHI_FINE_PERMUTATION_V1.json (pooled).
Writes D2_FLOOR_TABLE_V1.json."""
from __future__ import annotations

import datetime as dt
import json
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SRC = Path(r"G:\visual_rebuild_v2\06_learning\mythos_presence_v1")
AUD = Path(r"G:\chappy_ai_storage\handoff\judge2026_submit_camera_ready_audit_v1")
OUT = Path(__file__).resolve().parent / "D2_FLOOR_TABLE_V1.json"
CUT = dt.datetime.fromisoformat("2026-08-22T09:00:00")
NS = (3, 4, 6, 12, 24, 36, 72, 144)
PAPER_TABLE = (0.82, 0.71, 0.58, 0.41, 0.29, 0.24, 0.17, 0.12)


def thr(n1, n2, phi, k=2.0):
    return k * math.sqrt(phi * 0.25 / n1 + phi * 0.25 / n2)


def w18_rate(rel):
    ok = n = 0
    for line in open(SRC / "mythos_relation_wave18_v1.jsonl", encoding="utf-8", errors="replace"):
        if not line.strip():
            continue
        r = json.loads(line)
        t = r.get("ts")
        if not t or dt.datetime.fromisoformat(t[:19]) > CUT:
            continue
        if r.get("model") != "mythos-4b-champion:q4km" or r.get("relation") != rel:
            continue
        if r.get("verdict") in {"ERROR", "TRUNCATED_NO_VISIBLE_OUTPUT", None, ""}:
            continue
        n += 1
        ok += r.get("verdict") == "USED_LATEST"
    return ok, n


phi_corr = json.loads((AUD / "A_PHI_FINE_PERMUTATION_V1.json").read_text(encoding="utf-8"))["pooled"]["phi_between_repeat"]
o3, n3 = w18_rate("R3_samefield")
o4, n4 = w18_rate("R4_overwrite")
res = {"id": "SUB70_CR_D2_FLOOR_TABLE_V1", "phi_corrected": phi_corr,
       "caseE": {"R3_ok_n": [o3, n3], "R4_ok_n": [o4, n4], "diff": round(abs(o3 / n3 - o4 / n4), 2)},
       "rows": {}}
for label, phi in (("phi_1.01_paper", 1.01), ("phi_corrected", phi_corr)):
    res["rows"][label] = {
        "table": [round(thr(n, n, phi), 2) for n in NS],
        "caseG_n6": round(thr(6, 6, phi), 2), "caseH_n4": round(thr(4, 4, phi), 2),
        "caseE": round(thr(n3, n4, phi), 2)}
    print(label, res["rows"][label])
p = res["rows"]["phi_1.01_paper"]
res["calibration_match"] = (tuple(p["table"]) == PAPER_TABLE and p["caseG_n6"] == 0.58
                            and p["caseH_n4"] == 0.71 and p["caseE"] == 0.07 and n4 == 384
                            and res["caseE"]["diff"] == 0.56)
bad = tuple(round(thr(n, n, 1.01, k=1.0), 2) for n in NS)
res["known_bad_factor1"] = {"table": bad, "reproduces_paper": bad == PAPER_TABLE}
print("caseE", res["caseE"], "| calibration:", res["calibration_match"], "| known-bad:", res["known_bad_factor1"])
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("wrote", OUT)
