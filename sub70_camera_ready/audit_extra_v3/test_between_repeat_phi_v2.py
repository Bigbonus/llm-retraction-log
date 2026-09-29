# -*- coding: utf-8 -*-
"""Negative tests for between_repeat_phi_v2.py: malformed data must be refused, never silently change a
denominator. Also shows V1 accepted the same malformed file and computed a number from fewer rows."""
import csv
import random
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import between_repeat_phi_v2 as M  # noqa: E402

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


results = []
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    write(good, td / "good.csv")
    rc, out, _ = run("between_repeat_phi_v2.py", td / "good.csv")
    results.append(("clean file accepted", rc == 0 and "rows given 108" in out))

    cases = {
        "bad correct value": good + [("c0", "0", "maybe")],
        "blank cell": good + [("", "0", "1")],
        "blank repeat": good + [("c0", "", "1")],
    }
    for name, rows in cases.items():
        write(rows, td / "bad.csv")
        rc2, out2, err2 = run("between_repeat_phi_v2.py", td / "bad.csv")
        rc1, out1, _ = run("between_repeat_phi.py", td / "bad.csv")
        results.append(("v2 refuses: " + name, rc2 == 2 and "line 110" in err2 and "phi" not in out2))
        results.append(("v1 silently dropped: " + name, rc1 == 0 and "cells used" in out1))

    write(good, td / "nocol.csv", header=("cell", "repeat", "score"))
    rc, out, err = run("between_repeat_phi_v2.py", td / "nocol.csv")
    results.append(("missing column refused", rc == 2 and "missing column" in err))

    # exclusion accounting: a ceiling cell and a tiny cell are reported, not hidden
    rows = good + [("ceil", "0", 1)] * 5 + [("ceil", "1", 1)] * 5 + [("tiny", "0", 1), ("tiny", "1", 0)]
    write(rows, td / "excl.csv")
    rc, out, _ = run("between_repeat_phi_v2.py", td / "excl.csv")
    results.append(("exclusions reported", rc == 0 and "'rate 0 or 1': 1" in out and "'fewer than 4 rows': 1" in out))

ok = all(r for _, r in results)
for name, r in results:
    print("%-40s %s" % (name, "ok" if r else "FAIL"))
print("NEGATIVE TESTS", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
