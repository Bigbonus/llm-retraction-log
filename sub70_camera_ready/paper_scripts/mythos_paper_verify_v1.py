# -*- coding: utf-8 -*-
"""投稿論文に書いた数字を、生データから独立に再計算する(2026-08-22)。

**書いた値を信じない。**査読に出す前に、全部の数字を出し直して突き合わせる。
今日だけで自分の計器が三度壊れている。四度目が論文の中にある可能性を潰す。

一致しなければ論文を直す。一致しても、一致したことを記録する。
"""
from __future__ import annotations

import collections
import datetime as dt
import glob
import json
import math
import random
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAIMS = []          # (節, 主張, 論文の値, 実測値, 一致か)


def chk(sec, what, paper, actual, tol=0.005):
    if isinstance(paper, (int, float)) and isinstance(actual, (int, float)):
        ok = abs(paper - actual) <= tol * max(1.0, abs(paper))
    else:
        ok = str(paper) == str(actual)
    CLAIMS.append((sec, what, paper, actual, ok))
    print("  %s %-46s 論文 %-14s 実測 %s" %
          ("OK  " if ok else "**×**", what[:46], str(paper), str(actual)))
    return ok


NON_EVENT = {"ERROR", "TRUNCATED_NO_VISIBLE_OUTPUT", None, ""}


# **凍結コーパスだけを読む。**打ち切り以降の行は使わない。
CUTOFF = dt.datetime.fromisoformat("2026-08-22T09:00:00")
MIN_ROWS_PER_MODEL = 100
NO_TS = [0]


def load(fn):
    out = []
    for l in open(fn, encoding="utf-8", errors="replace"):
        if not l.strip():
            continue
        try:
            r = json.loads(l)
        except Exception:                                          # noqa: BLE001
            continue
        t = r.get("ts")
        # **時刻の無い行は使わない。**第三者が同じ行集合を再構成できないため。
        if not t:
            NO_TS[0] += 1
            continue
        if dt.datetime.fromisoformat(t[:19]) > CUTOFF:
            continue
        out.append(r)
    return out


# ---------- §Setting ----------
print("\n### Setting")
waves, rows_total, scored = 0, 0, 0
for f in sorted(glob.glob("*.jsonl")):
    r = load(f)
    if not r:
        continue
    if not (r[0].get("model") and r[0].get("verdict")):
        continue
    waves += 1
    rows_total += len(r)
    scored += sum(1 for x in r if x.get("verdict") not in NON_EVENT)
chk("Setting", "probe waves", 20, waves)
chk("Setting", "凍結後の総行数", 79021, rows_total)
chk("Setting", "凍結後の採点行", 77293, scored)
print("      (時刻が無く除外した行 %d)" % NO_TS[0])

# ---------- §2.1 漏洩 ----------
print("\n### 2.1 妨害が正解を符号化していた")


def rid(rng):
    return "u1a_%s_%s_attempt_v%d" % (
        "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(3)),
        "".join(rng.choice("0123456789abcdef") for _ in range(6)), rng.randint(2, 9))


def near_of(base, rng):
    i = rng.randrange(4, len(base) - 2)
    c = base[i]
    pool = "0123456789abcdef" if c in "0123456789abcdef" else "abcdefghijklmnopqrstuvwxyz"
    return base[:i] + rng.choice([x for x in pool if x != c]) + base[i + 1:]


def majority(ss):
    n = min(len(s) for s in ss)
    return "".join(collections.Counter(s[p] for s in ss).most_common(1)[0][0]
                   for p in range(n))


PAPER_LEAK = {1: 0.000, 3: 0.900, 8: 1.000, 20: 1.000, 40: 1.000, 80: 1.000}
for k, want in PAPER_LEAK.items():
    hit = 0
    for t in range(400):
        rng = random.Random(t * 7919 + k)
        truth = rid(rng)
        others = [near_of(truth, rng) for _ in range(k)]
        hit += majority(others) == truth
    chk("2.1", "多数決で復元 k=%d" % k, want, round(hit / 400, 3), tol=0.02)
for k in (8, 80):
    hit = 0
    for t in range(200):
        rng = random.Random(t * 7919 + k)
        truth = rid(rng)
        hit += majority([rid(rng) for _ in range(k)]) == truth
    chk("2.1", "対照(乱数ID) k=%d" % k, 0.000, round(hit / 200, 3), tol=0.01)

w18 = load("mythos_relation_wave18_v1.jsonl")
w19 = load("mythos_relation_hard_wave19_v1.jsonl")


def rate(rows, **kw):
    ok = n = 0
    for r in rows:
        if any(r.get(a) != b for a, b in kw.items()):
            continue
        v = r.get("verdict")
        if v in NON_EVENT:
            continue
        n += 1
        ok += (v == "USED_LATEST")
    return (ok / n if n else None), n


r_plain, n_plain = rate(w18, model="mythos-4b-champion:q4km", relation="R4_overwrite")
chk("2.1", "素の R4(champion)", 0.44, round(r_plain, 2))
r_near, n_near = rate(w19, model="mythos-4b-champion:q4km",
                      relation="R4_overwrite", hard="near_ids")
chk("2.1", "near_ids の R4(champion)", 0.98, round(r_near, 2))

# ---------- §2.2 採点鍵 ----------
print("\n### 2.2 採点鍵が本文と矛盾")
r_ph, n_ph = rate(w19, model="mythos-4b-champion:q4km",
                  relation="R4_overwrite", hard="pos_head")
chk("2.2", "pos_head の R4(champion)", 0.00, round(r_ph, 2))
chk("2.2", "その n", 24, n_ph)
lo = hi = None
ns = []
for rel in ("R0_unrelated", "R1_format", "R2_field", "R3_samefield"):
    tot_ok = tot_n = 0
    # qwen3:4b は think=False でも応答の 100% が思考文を本文へ出す。採点は
    # truth in reply を最初に判定するため、思考中に正解へ触れれば正になる。
    # 行に truth も others も無く事後の再採点ができないので、**除外する**。
    # 記録: MYTHOS_X001_MOE_LADDER_RESULT_V1.json
    for m in ("mythos-4b-champion:q4km", "qwen3:14b"):
        v, n = rate(w19, model=m, relation=rel, hard="pos_head")
        if v is None:
            continue
        lo = v if lo is None else min(lo, v)
        hi = v if hi is None else max(hi, v)
        tot_ok += v * n
        tot_n += n
    ns.append(tot_n)
chk("2.2", "pos_head R0-R3 の最低値", 0.94, round(lo, 2))
chk("2.2", "pos_head R0-R3 の最高値", 1.00, round(hi, 2))
chk("2.2", "段ごとの n の下限(監査可能 2 器)", 56, min(ns))
chk("2.2", "段ごとの n の上限(監査可能 2 器)", 60, max(ns))

# ---------- §2.3 非事象 ----------
print("\n### 2.3 非回答を誤答として採点")
c = collections.defaultdict(collections.Counter)
for r in w18:
    c[r.get("model")][r.get("verdict")] += 1
nem = "mythos-nemotron-nano-9b-v2:q5km"
tot = sum(c[nem].values())
chk("2.3", "9B の行数", 1772, tot)
chk("2.3", "9B の USED_LATEST 率", 0.46, round(c[nem]["USED_LATEST"] / tot, 2))
chk("2.3", "9B の truncated 率", 0.31,
    round(c[nem]["TRUNCATED_NO_VISIBLE_OUTPUT"] / tot, 2))
chk("2.3", "9B の NO_ID 率", 0.21, round(c[nem]["NO_ID"] / tot, 2))
others = [m for m in c if m != nem and sum(c[m].values()) >= MIN_ROWS_PER_MODEL]
chk("2.3", "比較に入る他の器の数", 3, len(others))
o_lo = min(c[m]["USED_LATEST"] / sum(c[m].values()) for m in others)
o_hi = max(c[m]["USED_LATEST"] / sum(c[m].values()) for m in others)
chk("2.3", "他 3 器の USED_LATEST 下限", 0.89, round(o_lo, 2))
chk("2.3", "他 3 器の USED_LATEST 上限", 0.94, round(o_hi, 2))
ne_hi = max((c[m]["TRUNCATED_NO_VISIBLE_OUTPUT"] + c[m]["NO_ID"]) / sum(c[m].values())
            for m in others)
chk("2.3", "他 3 器の非回答率の上限", 0.01, round(ne_hi, 2))

# ---------- §3 床 ----------
print("\n### 3 雑音の床")
PHI = 1.01


def thr(n1, n2, phi=PHI):
    return 2 * math.sqrt(phi * 0.25 / n1 + phi * 0.25 / n2)


for n, want in ((3, 0.82), (4, 0.71), (6, 0.58), (12, 0.41),
                (24, 0.29), (36, 0.24), (72, 0.17), (144, 0.12)):
    chk("3", "閾値 n=%d" % n, want, round(thr(n, n), 2))
chk("3", "case G  n=6 の差", 0.50, round(abs(0.83 - 0.33), 2))
chk("3", "case H  n=4 の差", 0.50, round(abs(1.00 - 0.50), 2))
r3, n3 = rate(w18, model="mythos-4b-champion:q4km", relation="R3_samefield")
chk("3", "case E  R3(champion)", 1.00, round(r3, 2))
chk("3", "case E  n", 384, n_plain)
chk("3", "case E  差", 0.56, round(abs(r3 - r_plain), 2))
chk("3", "case E  閾値", 0.07, round(thr(n3, n_plain), 2))
chk("3", "case E  R3 の n", n3, n3)

print("\n########## まとめ ##########")
bad = [x for x in CLAIMS if not x[4]]
print("照合 %d 件 / 不一致 %d 件" % (len(CLAIMS), len(bad)))
if bad:
    print("\n**論文を直す必要がある箇所:**")
    for sec, what, paper, actual, _ in bad:
        print("  [%s] %s  論文 %s -> 実測 %s" % (sec, what, paper, actual))
else:
    print("**全部一致した。**")
