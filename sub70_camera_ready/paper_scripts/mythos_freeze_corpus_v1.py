# -*- coding: utf-8 -*-
"""投稿用にコーパスを凍結する(2026-08-22)。

検証で 8 件の不一致が出た。原因は計算違いではなく **データが動いたこと**。
波が走り続けている限り、論文の数字は書いた翌分には古くなる。
さらに、supervisor が起こした 5 器目が 4 行だけ混じり、
「他 3 器」という記述を壊していた。

**凍結する。**
  - 打ち切り時刻を決め、それ以降の行は使わない
  - 使うファイルの SHA256 と行数を記録する
  - 器レベルの比較には最小行数の規則を置く(少数行の器を黙って混ぜない)

凍結表は論文に載せ、第三者が同じ行集合を再構成できるようにする。
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CUTOFF = "2026-08-22T09:00:00"
MIN_ROWS_PER_MODEL = 100          # 器レベルの比較に入れる下限
OUT = "MYTHOS_PAPER_CORPUS_FREEZE_V1.json"
NON_EVENT = {"ERROR", "TRUNCATED_NO_VISIBLE_OUTPUT", None, ""}


def main() -> int:
    cut = dt.datetime.fromisoformat(CUTOFF)
    files = {}
    waves = 0
    rows_total = rows_scored = 0
    for fn in sorted(glob.glob("*.jsonl")):
        raw = open(fn, "rb").read()
        rows = []
        for l in raw.decode("utf-8", "replace").splitlines():
            if not l.strip():
                continue
            try:
                r = json.loads(l)
            except Exception:                                      # noqa: BLE001
                continue
            rows.append(r)
        if not rows or not (rows[0].get("model") and rows[0].get("verdict")):
            continue
        kept = [r for r in rows
                if r.get("ts") and dt.datetime.fromisoformat(r["ts"][:19]) <= cut]
        if not kept:
            continue
        waves += 1
        rows_total += len(kept)
        rows_scored += sum(1 for r in kept if r.get("verdict") not in NON_EVENT)
        models = {}
        for r in kept:
            models[r.get("model")] = models.get(r.get("model"), 0) + 1
        files[fn] = {
            "sha256_full_file": hashlib.sha256(raw).hexdigest(),
            "rows_in_file": len(rows),
            "rows_at_or_before_cutoff": len(kept),
            "models": models,
            "models_below_min": {m: n for m, n in models.items()
                                 if n < MIN_ROWS_PER_MODEL},
        }

    doc = {
        "id": "PAPER_CORPUS_FREEZE_V1",
        "cutoff_ts": CUTOFF,
        "rule": ("この時刻以前の ts を持つ行だけを使う。ファイル全体の SHA256 は"
                 "凍結後も波が追記されうるため、**行の再構成は ts で行う**。"),
        "min_rows_per_model": MIN_ROWS_PER_MODEL,
        "why_min_rows": ("supervisor が起こした 5 器目が 4 行だけ混じり、"
                         "『他 3 器』という記述を壊した。少数行の器を黙って"
                         "混ぜない。**除外したことは表に残す。**"),
        "waves": waves,
        "rows_total": rows_total,
        "rows_scored": rows_scored,
        "files": files,
    }
    open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(doc, ensure_ascii=False, indent=1))

    print("打ち切り %s" % CUTOFF)
    print("波 %d / 行 %d(うち採点行 %d)" % (waves, rows_total, rows_scored))
    print("\n最小行数に満たず除外される器:")
    any_ex = False
    for fn, d in files.items():
        for m, n in d["models_below_min"].items():
            print("  %-42s %-46s %d 行" % (fn[:42], str(m)[:46], n))
            any_ex = True
    if not any_ex:
        print("  なし")
    print("\n書き出し: %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
