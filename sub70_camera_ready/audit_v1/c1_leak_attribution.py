# -*- coding: utf-8 -*-
"""Objection C: does the logged model behaviour follow the leak mechanism?

The near_ids condition (W19 runner, build()): gold line is LAST, k distractors
each differ from gold at one random position. Position-wise majority of the
distractors equals the gold only for k >= 3 (paper table: k=1 0.000, k=3
0.900, k>=8 1.000). At k=1 the majority IS the single distractor, so a model
that decodes the majority would answer the distractor (verdict USED_OLDER).
At k=3 a failed majority yields a string that is neither gold nor a
distractor (verdict OTHER_ID). Truth/others are NOT logged in W19 rows, so
item-level majority cannot be recomputed; only these k-level predictions can
be tested.

 1. CALIBRATE: reproduce the paper's 0.44 (W18 plain R4, champion) and 0.98
    (W19 near_ids R4, champion), and the Appendix B leak table.
 2. KNOWN-BAD: majority() fed independent random ids must give 0.000.
 3. Per model x relation x k: accuracy and verdict mix in near_ids vs plain.
 4. Number of IDs in replies (echoing a list can score as correct).
Writes C_LEAK_RESULT_V1.json."""
from __future__ import annotations

import collections
import random
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, __file__.rsplit("\\", 1)[0])
import audit_common as C  # noqa: E402

W18 = "mythos_relation_wave18_v1.jsonl"
W19 = "mythos_relation_hard_wave19_v1.jsonl"
IDRE = re.compile(r"u1a_[a-z]{3}_[0-9a-f]{6}_attempt_v\d")
CH = "mythos-4b-champion:q4km"


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
    return "".join(collections.Counter(s[p] for s in ss).most_common(1)[0][0] for p in range(n))


def leak_table(gen_near=True, trials=400):
    out = {}
    for k in (1, 3, 8, 20, 40, 80):
        hit = 0
        maj_is_other = 0
        for t in range(trials):
            rng = random.Random(t * 7919 + k)
            truth = rid(rng)
            others = [near_of(truth, rng) if gen_near else rid(rng) for _ in range(k)]
            m = majority(others)
            hit += m == truth
            maj_is_other += (m != truth and m in others)
        out[k] = (round(hit / trials, 3), round(maj_is_other / trials, 3))
    return out


def rate(rows, **kw):
    ok = n = 0
    for r in rows:
        if any(r.get(a) != b for a, b in kw.items()):
            continue
        if r.get("verdict") in C.NON_EVENT:
            continue
        n += 1
        ok += r.get("verdict") == "USED_LATEST"
    return (ok / n if n else None), n


def main() -> int:
    res = {"id": "SUB70_AUDIT_C_LEAK_V1",
           "sha256": {W18: C.sha256_file(C.SRC / W18), W19: C.sha256_file(C.SRC / W19)}}
    w18, w19 = C.load(W18), C.load(W19)
    print("### 1. calibration")
    r18, n18 = rate(w18, model=CH, relation="R4_overwrite")
    r19, n19 = rate(w19, model=CH, relation="R4_overwrite", hard="near_ids")
    lt = leak_table(True)
    want = {1: 0.0, 3: 0.9, 8: 1.0, 20: 1.0, 40: 1.0, 80: 1.0}
    ok = (round(r18, 2) == 0.44 and round(r19, 2) == 0.98
          and all(abs(lt[k][0] - want[k]) <= 0.02 for k in want))
    print("  W18 plain R4 champion %.4f (n %d) paper 0.44 | W19 near_ids R4 champion %.4f (n %d) paper 0.98"
          % (r18, n18, r19, n19))
    print("  leak table (P(majority=gold), P(majority=one of the distractors)):", lt)
    kb = leak_table(False, 200)
    print("  known-bad (independent random ids):", kb)
    ok_kb = all(v[0] == 0.0 for v in kb.values())
    res["calibration"] = {"w18_plain_R4_champion": [r18, n18], "w19_near_R4_champion": [r19, n19],
                          "leak_table": lt, "match": ok, "known_bad_random_ids": kb,
                          "known_bad_gives_zero": ok_kb}

    print("\n### 2. W19 conditions present (frozen rows)")
    cond = collections.Counter((r.get("hard"), r.get("model"), r.get("temperature")) for r in w19)
    for k, v in sorted(cond.items(), key=str):
        print("  ", k, v)
    res["w19_conditions"] = {"|".join(map(str, k)): v for k, v in cond.items()}

    print("\n### 3. per k: accuracy and verdicts, near_ids vs plain (W18) vs pos_head, R4 and R0-R3")
    tab = {}
    for src, rows, hard in (("W18_plain", w18, None), ("W19_near_ids", w19, "near_ids"),
                            ("W19_pos_head", w19, "pos_head")):
        for r in rows:
            if hard and r.get("hard") != hard:
                continue
            key = (src, r.get("model"), r.get("relation") == "R4_overwrite", r.get("amount"))
            d = tab.setdefault(key, collections.Counter())
            d[r.get("verdict")] += 1
            d["cap"] += r.get("done_reason") == "length"
            ids = IDRE.findall(r.get("reply") or "")
            d["ids_ge2"] += len(set(ids)) >= 2
    out3 = {}
    for key in sorted(tab, key=str):
        d = tab[key]
        sc = sum(v for k, v in d.items() if k not in ("cap", "ids_ge2") and k not in C.NON_EVENT)
        acc = d["USED_LATEST"] / sc if sc else None
        out3["|".join(map(str, key))] = dict(d, scored=sc, acc=None if acc is None else round(acc, 4))
        if key[1] in (CH, "qwen3:14b", "qwen3:4b"):
            print("  %-13s %-24s R4=%-5s k=%-3s scored %4d acc %s  OLDER %d OTHER_ID %d NO_ID %d  multi-id replies %d cap %d"
                  % (key[0], str(key[1])[:24], key[2], key[3], sc,
                     None if acc is None else "%.3f" % acc, d["USED_OLDER"], d["OTHER_ID"],
                     d["NO_ID"], d["ids_ge2"], d["cap"]))
    res["per_k"] = out3
    p = C.write_json("C_LEAK_RESULT_V1.json", res)
    print("\nwrote", p)
    return 0 if (ok and ok_kb) else 2


if __name__ == "__main__":
    raise SystemExit(main())
