# -*- coding: utf-8 -*-
"""この計器の雑音の床を測る(2026-08-22)。

棚卸しで repeat が 12 ファイルに記録されていて一度も使われていないと分かった。
**同じセルを繰り返し測ったぶんが、そのまま眠っている。**

同一セル(器 x 条件 x 量 x 温度)の中で、繰り返しだけが違う行を集めれば、
何も変えていないのに出る差 = **雑音**が測れる。

これが分かると:
  - 床より小さい差は、どんなに綺麗でも読んではいけない
  - 必要な n を後から言い訳せずに決められる
  - 過去の主張を床に照らして再点検できる

出すもの: セル内の二項分散を超える余剰分散(over-dispersion)。
  phi = 1.0 なら、ばらつきは二項分布どおり(追加の雑音なし)
  phi > 1.0 なら、**同じ条件でも余分に暴れている**
"""
from __future__ import annotations

import collections
import json
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = Path(__file__).resolve().parent
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
# セルを決める列。**repeat と seed は除く**(それが動かす軸だから)
CELL_KEYS = ("model", "relation", "amount", "temperature", "condition", "mode",
             "hard", "task", "item", "persona", "json_format", "abstain_rule",
             "position", "answerable", "lines")


def main() -> int:
    print("### 同じセルを繰り返したときの、余分なばらつき\n")
    print("phi = 実測分散 / 二項分散。**1.0 なら追加の雑音なし。**\n")
    print("%-42s %6s %8s %8s %8s" % ("wave", "セル", "平均n", "phi", "床(±)"))
    out = []
    for p in sorted(D.glob("*.jsonl")):
        if p.name in SKIP:
            continue
        cells = collections.defaultdict(list)
        for line in p.open(encoding="utf-8", errors="replace"):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:                                      # noqa: BLE001
                continue
            if not _in_freeze(r):
                continue
            if "repeat" not in r or r.get("verdict") in NON_EVENT:
                continue
            c = r.get("correct")
            if not isinstance(c, bool):
                continue
            key = tuple((k, r.get(k)) for k in CELL_KEYS if k in r)
            cells[key].append(1 if c else 0)
        usable = {k: v for k, v in cells.items() if len(v) >= 4}
        if len(usable) < 5:
            continue
        # Pearson chi2 / df による過分散
        chi2 = 0.0
        df = 0
        ns = []
        for v in usable.values():
            n = len(v)
            ns.append(n)
            phat = sum(v) / n
            if phat in (0.0, 1.0):
                continue                                           # 天井/床は情報が無い
            exp_var = phat * (1 - phat) / n
            obs = sum((x - phat) ** 2 for x in v) / (n - 1) / n
            chi2 += obs / exp_var
            df += 1
        if df < 5:
            print("%-42s %6d %8.1f %8s %8s" %
                  (p.name[:42], len(usable), sum(ns) / len(ns), "全て天井/床", "-"))
            continue
        phi = chi2 / df
        # 床: 平均セル n における 1 標準誤差(過分散込み)を p=0.5 で評価
        nbar = sum(ns) / len(ns)
        floor = math.sqrt(phi * 0.25 / nbar)
        out.append((p.name, len(usable), nbar, phi, floor))
        print("%-42s %6d %8.1f %8.2f %8.3f" % (p.name[:42], len(usable), nbar, phi, floor))

    if out:
        phis = sorted(o[3] for o in out)
        med = phis[len(phis) // 2]
        print("\n過分散 phi の中央値 = %.2f" % med)
        if med <= 1.15:
            print("**セル内のばらつきは、ほぼ二項分布どおり。**"
                  "同一条件の繰り返しに余分な暴れは無い。")
        else:
            print("**二項分布より %.0f%% 余分に暴れている。**"
                  "同じ条件でも結果が動く。n の計算はこれを掛けて行うこと。" % ((med - 1) * 100))
        print("\n目安: セル n=%d のとき、**±%.3f より小さい差は読まない。**"
              % (12, math.sqrt(med * 0.25 / 12)))
        print("      セル n=%d なら ±%.3f" % (36, math.sqrt(med * 0.25 / 36)))
        print("      セル n=%d なら ±%.3f" % (144, math.sqrt(med * 0.25 / 144)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
