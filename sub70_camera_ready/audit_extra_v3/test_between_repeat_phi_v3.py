# -*- coding: utf-8 -*-
"""Tests for between_repeat_phi_v3.py. Labels distinguish (per Codex) a version that ACCEPTS a file
containing invalid rows from one that silently DROPS invalid outcomes; V1 does both depending on case.
Each refusal case names the line it expects in the error. Parity: V3 and V2 give the same phi on the
same clean file."""
import csv
import random
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
rng = random.Random(1)
good = [("c%d" % c, str(r), rng.randint(0, 1)) for c in range(6) for r in range(3) for _ in range(6)]


def write(rows, path, header=("cell", "repeat", "correct")):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def run(script, path):
    p = subprocess.run([sys.executable, str(HERE / script), str(path)], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def phi_line(out):
    return [ln for ln in out.splitlines() if ln.startswith("cells used")]


results = []
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    write(good, td / "good.csv")
    rc3, out3, _ = run("between_repeat_phi_v3.py", td / "good.csv")
    rc2, out2, _ = run("between_repeat_phi_v2.py", td / "good.csv")
    results.append(("clean file accepted by v3", rc3 == 0 and "rows given 108" in out3))
    results.append(("v3 phi line equals v2 phi line", phi_line(out3) == phi_line(out2)))

    refusals = {
        "bad correct value": (good + [("c0", "0", "maybe")], "line 110"),
        "blank cell": (good + [("", "0", "1")], "line 110"),
        "blank repeat": (good + [("c0", "", "1")], "line 110"),
        "surplus field in a row": (good + [("c0", "0", "1", "extra")], "line 110: 4 fields"),
        "missing field in a row": (good + [("c0", "0")], "line 110: 2 fields"),
    }
    for name, (rows, expect) in refusals.items():
        write(rows, td / "bad.csv")
        rc, out, err = run("between_repeat_phi_v3.py", td / "bad.csv")
        results.append(("v3 refuses: " + name, rc == 2 and expect in err and not phi_line(out)))
    # V1 behaviour on the same files, labelled by what it actually does
    write(good + [("c0", "0", "maybe")], td / "v1a.csv")
    rc, out, _ = run("between_repeat_phi.py", td / "v1a.csv")
    results.append(("v1 silently drops an invalid outcome", rc == 0 and bool(phi_line(out))))
    write(good + [("", "0", "1")], td / "v1b.csv")
    rc, out, _ = run("between_repeat_phi.py", td / "v1b.csv")
    results.append(("v1 accepts a blank cell id as a group", rc == 0 and bool(phi_line(out))))

    write(good, td / "dup.csv", header=("Cell", "repeat", "correct", "cell"))
    with open(td / "dup.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh); w.writerow(("Cell", "repeat", "correct", "cell")); w.writerows([r + ("x",) for r in good])
    rc, out, err = run("between_repeat_phi_v3.py", td / "dup.csv")
    results.append(("duplicate normalised header refused", rc == 2 and "appears 2 times" in err))
    write(good, td / "nocol.csv", header=("cell", "repeat", "score"))
    rc, out, err = run("between_repeat_phi_v3.py", td / "nocol.csv")
    results.append(("missing column refused", rc == 2 and "missing column" in err))

    rows = good + [("ceil", "0", 1)] * 5 + [("ceil", "1", 1)] * 5 + [("tiny", "0", 1), ("tiny", "1", 0)]
    write(rows, td / "excl.csv")
    rc, out, _ = run("between_repeat_phi_v3.py", td / "excl.csv")
    results.append(("exclusions reported by reason", rc == 0 and "'rate 0 or 1': 1" in out and "'fewer than 4 rows': 1" in out))

ok = all(r for _, r in results)
for name, r in results:
    print("%-44s %s" % (name, "ok" if r else "FAIL"))
print("%d checks, %s" % (len(results), "PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
