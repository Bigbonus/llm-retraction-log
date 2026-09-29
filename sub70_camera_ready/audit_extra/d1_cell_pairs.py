# -*- coding: utf-8 -*-
"""Recompute the paper's corpus-wide "cell pairs readable" figure.

Re-implements G:\\visual_rebuild_v2\\06_learning\\mythos_presence_v1\\
mythos_claim_audit_v1.py (sha256 prefix recorded in the output) on the
frozen rows. CALIBRATE: with phi = 1.01 it must reproduce the paper's
46,279 pairs / 8,008 readable (17.3%) / 639 pairs with diff >= 0.30 that the
floor rejects. KNOWN-BAD: without the cutoff it must not reproduce them.
Then report the same enumeration at phi = 1.00 and at the corrected
between-repeat estimate 1.076 (A_PHI_FINE_PERMUTATION_V1.json, pooled).
Writes D1_CELL_PAIRS_V1.json next to this script."""
from __future__ import annotations

import collections
import datetime as dt
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SRC = Path(r"G:\visual_rebuild_v2\06_learning\mythos_presence_v1")
AUD = Path(r"G:\chappy_ai_storage\handoff\judge2026_submit_camera_ready_audit_v1")
OUT = Path(__file__).resolve().parent / "D1_CELL_PAIRS_V1.json"
SKIP = {"_queue.jsonl", "_queue_done.jsonl", "_queue_dropped.jsonl",
        "_queue_failed_launch.jsonl", "MYTHOS_RETRACTIONS_V1.jsonl"}
NON_EVENT = {"ERROR", "TRUNCATED_NO_VISIBLE_OUTPUT", None, ""}
FACET = ("relation", "amount", "condition", "mode", "hard", "task",
         "persona", "json_format", "abstain_rule", "answerable", "lines")
CUT = dt.datetime.fromisoformat("2026-08-22T09:00:00")
FAR = dt.datetime.fromisoformat("2100-01-01T00:00:00")
PAPER = (46279, 8008, 639)


def cells_by_wave(cutoff):
    out = {}
    for p in sorted(SRC.glob("*.jsonl")):
        if p.name in SKIP:
            continue
        cells = collections.defaultdict(lambda: [0, 0])
        for line in p.open(encoding="utf-8", errors="replace"):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            t = r.get("ts")
            if not t:
                continue
            try:
                if dt.datetime.fromisoformat(t[:19]) > cutoff:
                    continue
            except Exception:  # noqa: BLE001
                continue
            if r.get("verdict") in NON_EVENT:
                continue
            c = r.get("correct")
            if not isinstance(c, bool) or not r.get("model"):
                continue
            key = (r["model"],) + tuple(str(r.get(k)) for k in FACET if k in r)
            cells[key][1] += 1
            cells[key][0] += c
        usable = {k: v for k, v in cells.items() if v[1] >= 3}
        if len(usable) >= 2:
            out[p.name] = usable
    return out


def enumerate_pairs(waves, phi):
    tot = ok = small = 0
    for usable in waves.values():
        for a, b in itertools.combinations(list(usable), 2):
            (oa, na), (ob, nb) = usable[a], usable[b]
            d = abs(oa / na - ob / nb)
            th = 2 * math.sqrt(phi * 0.25 / na + phi * 0.25 / nb)
            tot += 1
            if d >= th:
                ok += 1
            elif d >= 0.30:
                small += 1
    return tot, ok, small


phi_corr = json.loads((AUD / "A_PHI_FINE_PERMUTATION_V1.json").read_text(encoding="utf-8"))["pooled"]["phi_between_repeat"]
frozen = cells_by_wave(CUT)
res = {"id": "SUB70_CR_D1_CELL_PAIRS_V1",
       "reimplements": "mythos_claim_audit_v1.py sha256 " + hashlib.sha256(
           (SRC / "mythos_claim_audit_v1.py").read_bytes()).hexdigest()[:12],
       "phi_corrected_source": "A_PHI_FINE_PERMUTATION_V1.json pooled.phi_between_repeat",
       "rows": {}}
for label, phi in (("phi_1.01_paper", 1.01), ("phi_1.00", 1.00), ("phi_corrected", phi_corr)):
    t, o, s = enumerate_pairs(frozen, phi)
    res["rows"][label] = {"phi": phi, "pairs": t, "readable": o, "share": round(o / t, 4),
                          "diff_ge_0.30_rejected": s}
    print(label, res["rows"][label])
cal = tuple(res["rows"]["phi_1.01_paper"][k] for k in ("pairs", "readable", "diff_ge_0.30_rejected"))
res["calibration_match"] = cal == PAPER
kb = enumerate_pairs(cells_by_wave(FAR), 1.01)
res["known_bad_no_cutoff"] = {"pairs": kb[0], "readable": kb[1], "rejected_ge_0.30": kb[2],
                              "reproduces_paper": kb == PAPER}
print("calibration match:", res["calibration_match"], "| known-bad (no cutoff):", kb)
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("wrote", OUT)
