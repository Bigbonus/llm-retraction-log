# -*- coding: utf-8 -*-
"""Shared read-only loader for the Sub70 camera-ready audit.

Reads the frozen corpus exactly as the paper's scripts define it:
rows whose `ts` is at or before 2026-08-22T09:00:00 (local, as written in
the rows). Rows without `ts` are dropped. Nothing is written to the source
directory; every file is opened read-only.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

SRC = Path(r"G:\visual_rebuild_v2\06_learning\mythos_presence_v1")
OUT = Path(__file__).resolve().parent
CUTOFF = dt.datetime.fromisoformat("2026-08-22T09:00:00")
NON_EVENT = {"ERROR", "TRUNCATED_NO_VISIBLE_OUTPUT", None, ""}
SKIP = {"_queue.jsonl", "_queue_done.jsonl", "_queue_dropped.jsonl",
        "_queue_failed_launch.jsonl", "MYTHOS_RETRACTIONS_V1.jsonl"}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def in_freeze(r, cutoff=CUTOFF) -> bool:
    t = r.get("ts")
    if not t:
        return False
    try:
        return dt.datetime.fromisoformat(t[:19]) <= cutoff
    except Exception:  # noqa: BLE001
        return False


def load(name: str, cutoff=CUTOFF, frozen_only=True):
    rows = []
    with open(SRC / name, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            if frozen_only and not in_freeze(r, cutoff):
                continue
            rows.append(r)
    return rows


def wave_files():
    return [p for p in sorted(SRC.glob("*.jsonl")) if p.name not in SKIP]


def write_json(name: str, obj) -> Path:
    p = OUT / name
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8",
                 newline="\n")
    return p
