# -*- coding: utf-8 -*-
"""Cross-check for Sec. 2.3 and the W18 temperature outlier: reproduce the
paper's non-answer numbers (calibration), then add the length-cap rate
(done_reason == "length") for every model the paper calls "the other three".
Known-bad: dropping the freeze cutoff must change the 1,772-row count.
Writes B_SEC23_CAP_V1.json."""
from __future__ import annotations

import collections
import datetime as dt
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, __file__.rsplit("\\", 1)[0])
import audit_common as C  # noqa: E402

W18 = "mythos_relation_wave18_v1.jsonl"
NEM = "mythos-nemotron-nano-9b-v2:q5km"


def table(rows):
    c = collections.defaultdict(collections.Counter)
    for r in rows:
        c[r.get("model")][r.get("verdict")] += 1
        c[r.get("model")]["_cap"] += r.get("done_reason") == "length"
        c[r.get("model")]["_rows"] += 1
    return c


c = table(C.load(W18))
tot = c[NEM]["_rows"]
got = {"rows_9b": tot, "acc_9b": round(c[NEM]["USED_LATEST"] / tot, 2),
       "trunc_9b": round(c[NEM]["TRUNCATED_NO_VISIBLE_OUTPUT"] / tot, 2),
       "noid_9b": round(c[NEM]["NO_ID"] / tot, 2)}
others = [m for m in c if m != NEM and c[m]["_rows"] >= 100]
acc_o = {m: round(c[m]["USED_LATEST"] / c[m]["_rows"], 4) for m in others}
nonans_o = {m: round((c[m]["TRUNCATED_NO_VISIBLE_OUTPUT"] + c[m]["NO_ID"]) / c[m]["_rows"], 4) for m in others}
cap = {m: [c[m]["_cap"], c[m]["_rows"], round(c[m]["_cap"] / c[m]["_rows"], 4)] for m in list(others) + [NEM]}
want = {"rows_9b": 1772, "acc_9b": 0.46, "trunc_9b": 0.31, "noid_9b": 0.21}
ok = (got == want and len(others) == 3 and round(min(acc_o.values()), 2) == 0.89
      and round(max(acc_o.values()), 2) == 0.94 and round(max(nonans_o.values()), 2) <= 0.01)
print("calibration (paper 2.3):", got, "others acc", acc_o, "others non-answer", nonans_o, "MATCH" if ok else "MISMATCH")
print("length-cap rate (done_reason == length):", cap)
cb = table(C.load(W18, cutoff=dt.datetime.fromisoformat("2100-01-01T00:00:00")))
kb_rows = cb[NEM]["_rows"]
print("known-bad (no cutoff): 9B rows", kb_rows, "reproduces 1772:", kb_rows == 1772)
print("wrote", C.write_json("B_SEC23_CAP_V1.json", {
    "id": "SUB70_AUDIT_B_SEC23_CAP_V1", "calibration": got, "match": ok,
    "others_acc": acc_o, "others_nonanswer_by_verdict": nonans_o,
    "length_cap_rate": cap, "known_bad_no_cutoff_9b_rows": kb_rows}))
