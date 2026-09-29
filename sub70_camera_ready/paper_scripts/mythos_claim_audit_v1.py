# -*- coding: utf-8 -*-
"""測った雑音の床を、手持ちのセル全部に当てる(2026-08-22)。

MYTHOS_NOISE_FLOOR_V1 で phi=1.01 が出た。そこから、
**二つのセルの差を読んでよい最小幅**が n ごとに決まる。

    閾値(n) = 2 * sqrt(2) * sqrt(phi * 0.25 / n)

この規則は既知の失敗 2 件(case G, H)に発火し、既知の正解 1 件
(case E)を通すことを確かめてある。

ここでは、**全波の全セル対に当てて、いくつが読める差なのか**を数える。
読めない差を根拠に書いた主張が他にもあるなら、いま見つけたい。

出すもの: 波ごとに、器の対・条件の対で、閾値を超えている対の割合。
"""
from __future__ import annotations

import collections
import itertools
import json
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = Path(__file__).resolve().parent
PHI = 1.01
SKIP = {"_queue.jsonl", "_queue_done.jsonl", "_queue_dropped.jsonl",
        "_queue_failed_launch.jsonl", "MYTHOS_RETRACTIONS_V1.jsonl"}
import datetime as _dt
CUTOFF = _dt.datetime.fromisoformat("2026-08-22T09:00:00")


def _in_freeze(r):
    """凍結コーパスの行か。**時刻の無い行は使わない。**"""
    t = r.get("ts")
    if not t:
        return False
    try:
        return _dt.datetime.fromisoformat(t[:19]) <= CUTOFF
    except Exception:                                              # noqa: BLE001
        return False


NON_EVENT = {"ERROR", "TRUNCATED_NO_VISIBLE_OUTPUT", None, ""}
FACET = ("relation", "amount", "condition", "mode", "hard", "task",
         "persona", "json_format", "abstain_rule", "answerable", "lines")


def thr(n1, n2):
    """二つのセルの差を読んでよい最小幅。**片側 n が違うときは合成する。**"""
    se = math.sqrt(PHI * 0.25 / n1 + PHI * 0.25 / n2)
    return 2 * se


def main() -> int:
    print("### 手持ちのセル対のうち、雑音の床を超えているのはどれだけか")
    print("床: phi=%.2f、閾値 = 2 * sqrt(0.25*phi/n1 + 0.25*phi/n2)\n" % PHI)
    print("%-42s %8s %8s %8s" % ("wave", "対の数", "読める", "割合"))
    tot_pair = tot_ok = 0
    small = []
    for p in sorted(D.glob("*.jsonl")):
        if p.name in SKIP:
            continue
        cells = collections.defaultdict(lambda: [0, 0])
        for line in p.open(encoding="utf-8", errors="replace"):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:                                      # noqa: BLE001
                continue
            if not _in_freeze(r):
                continue
            if r.get("verdict") in NON_EVENT:
                continue
            c = r.get("correct")
            if not isinstance(c, bool) or not r.get("model"):
                continue
            key = (r["model"],) + tuple(str(r.get(k)) for k in FACET if k in r)
            cells[key][1] += 1
            if c:
                cells[key][0] += 1
        usable = {k: v for k, v in cells.items() if v[1] >= 3}
        if len(usable) < 2:
            continue
        keys = list(usable)
        pairs = ok = 0
        for a, b in itertools.combinations(keys, 2):
            oa, na = usable[a]
            ob, nb = usable[b]
            pairs += 1
            d = abs(oa / na - ob / nb)
            if d >= thr(na, nb):
                ok += 1
            elif d >= 0.30:
                small.append((p.name, d, na, nb, thr(na, nb)))
        tot_pair += pairs
        tot_ok += ok
        print("%-42s %8d %8d %7.1f%%" % (p.name[:42], pairs, ok, 100 * ok / pairs))

    print("\n合計 %d 対のうち %d 対(%.1f%%)が床を超えている"
          % (tot_pair, tot_ok, 100 * tot_ok / max(1, tot_pair)))
    print("\n### 目を引くが読めない差(0.30 以上あるのに閾値未満)")
    if not small:
        print("  なし")
    else:
        print("  **%d 件。**大きく見えるのに n が足りていない対。" % len(small))
        for name, d, na, nb, t in sorted(small, key=lambda x: -x[1])[:12]:
            print("    %-38s 差 %.2f (n=%d,%d) 閾値 %.2f" % (name[:38], d, na, nb, t))
        print("\n  **こういう対を根拠に書いた文章が無いか、確かめること。**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
