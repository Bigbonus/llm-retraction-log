# -*- coding: utf-8 -*-
"""波をまたいだ未使用因子の解析 v1(2026-08-22)。

棚卸しで、**全波で記録してあるのに一度も集計されていない列**が出た。
temperature が 18 ファイル、chars が 21 ファイル、seed が 16 ファイル。
新しい測定は要らない。**既に測ってある。**

方法は医学のメタ解析をそのまま使う。波ごとに 2x2 を組んでログオッズ比を出し、
逆分散重みで併合、DerSimonian-Laird で異質性を見る。波は互いに設計が違うので
固定効果ではなく変量効果が正しい。

使い方:
    python mythos_cross_wave_v1.py --factor temperature
    python mythos_cross_wave_v1.py --factor chars       (長さは中央値で二分)
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = Path(__file__).resolve().parent

# 正解を表す列は波によって違う。**片方しか無い波もあるので両方見る。**
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


# 非事象は成功にも失敗にも数えない。**測っていないものを 0 として混ぜない。**
NON_EVENT = {"ERROR", "TRUNCATED_NO_VISIBLE_OUTPUT", None, ""}


def outcome(r):
    """その行が正解かどうか。判定できなければ None。"""
    v = r.get("verdict")
    if v in NON_EVENT:
        return None
    c = r.get("correct")
    if isinstance(c, bool):
        return c
    if v is not None:
        return v in ("USED_LATEST", "CORRECT", "OK", "PASS")
    return None


def log_or(a, b, c, d):
    """ログオッズ比と分散。Haldane-Anscombe 補正(0 セルがあるとき +0.5)。"""
    if min(a, b, c, d) == 0:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    lo = math.log((a * d) / (b * c))
    var = 1 / a + 1 / b + 1 / c + 1 / d
    return lo, var


def pool(rows):
    """DerSimonian-Laird 変量効果。"""
    w = [1 / v for _, v in rows]
    fe = sum(x * wi for (x, _), wi in zip(rows, w)) / sum(w)
    Q = sum(wi * (x - fe) ** 2 for (x, _), wi in zip(rows, w))
    k = len(rows)
    if k > 1:
        c = sum(w) - sum(wi ** 2 for wi in w) / sum(w)
        tau2 = max(0.0, (Q - (k - 1)) / c) if c > 0 else 0.0
    else:
        tau2 = 0.0
    w2 = [1 / (v + tau2) for _, v in rows]
    re = sum(x * wi for (x, _), wi in zip(rows, w2)) / sum(w2)
    se = math.sqrt(1 / sum(w2))
    I2 = max(0.0, (Q - (k - 1)) / Q) * 100 if Q > 0 and k > 1 else 0.0
    return re, se, Q, I2, tau2, k


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--factor", default="temperature")
    ap.add_argument("--min-cell", type=int, default=10,
                    help="1 セルの下限。**小さすぎるセルは併合に入れない**")
    args = ap.parse_args()

    per_wave = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    nonevent = collections.Counter()
    for p in sorted(D.glob("*.jsonl")):
        if p.name in SKIP:
            continue
        for line in p.open(encoding="utf-8", errors="replace"):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:                                      # noqa: BLE001
                continue
            if not _in_freeze(r):
                continue
            if args.factor not in r:
                continue
            ok = outcome(r)
            if ok is None:
                nonevent[p.name] += 1
                continue
            key = r[args.factor]
            if args.factor == "chars":
                key = "long" if (key or 0) >= 400 else "short"
            per_wave[p.name][key][1] += 1
            if ok:
                per_wave[p.name][key][0] += 1

    print("### 因子 = %s\n" % args.factor)
    print("%-42s %-10s %8s %8s" % ("wave", "水準", "正答率", "n"))
    studies = []
    for wave in sorted(per_wave):
        lv = per_wave[wave]
        levels = sorted(lv, key=str)
        if len(levels) < 2:
            continue
        shown = False
        for k in levels:
            ok, n = lv[k]
            if n < args.min_cell:
                continue
            print("%-42s %-10s %8.3f %8d" % (wave[:42] if not shown else "", str(k), ok / n, n))
            shown = True
        # 2 水準ちょうどのときだけ 2x2 が組める
        usable = [k for k in levels if lv[k][1] >= args.min_cell]
        if len(usable) == 2:
            (o1, n1), (o2, n2) = lv[usable[0]], lv[usable[1]]
            lo, var = log_or(o2, n2 - o2, o1, n1 - o1)
            studies.append(((lo, var), wave, usable))
        if shown:
            print()

    if len(studies) < 2:
        print("併合できる波が %d 本しかない。**併合しない。**" % len(studies))
        return 0

    re, se, Q, I2, tau2, k = pool([s[0] for s in studies])
    lo95, hi95 = re - 1.96 * se, re + 1.96 * se
    z = re / se
    print("########## 変量効果での併合(DerSimonian-Laird) ##########")
    print("  波の数 k = %d" % k)
    print("  参照水準 = %s、比較水準 = %s(波ごとに同じ向きで組んだ)"
          % (studies[0][2][0], studies[0][2][1]))
    print("  OR = %.3f  95%%CI [%.3f, %.3f]  z = %.2f" %
          (math.exp(re), math.exp(lo95), math.exp(hi95), z))
    print("  異質性 Q = %.1f  I2 = %.0f%%  tau2 = %.4f" % (Q, I2, tau2))
    if lo95 <= 0 <= hi95:
        print("\n  **信頼区間が 1 をまたぐ。差は立たない。**")
    else:
        print("\n  **区間が 1 を外れる。**ただし波の設計はそろっていないので、"
              "I2 が高ければ併合値そのものより、ばらつきの理由を見るほうが先。")

    # 各波の寄与
    print("\n  波ごとの OR:")
    for (lo, var), wave, usable in sorted(studies, key=lambda s: s[0][0]):
        print("    %-42s OR %6.2f  (1/var %6.1f)" % (wave[:42], math.exp(lo), 1 / var))

    if nonevent:
        print("\n  非事象として除外した行(成功にも失敗にも数えていない):")
        for w, c in nonevent.most_common(6):
            print("    %-42s %d" % (w[:42], c))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
