# -*- coding: utf-8 -*-
"""Clean-checkout check for between_repeat_phi_v3.py. Relative paths only; no dependency outside this
repository and the Python standard library. Run from anywhere:

    python sub70_camera_ready/audit_extra_v3/examples/run_examples.py

It builds the toy CSVs deterministically (so they are also committed for reading), runs the estimator
on each, and compares every line of output with EXPECTED_OUTPUT.txt. Exit 0 only on exact match.
A pass on a fresh checkout on the author's machine proves the files are self-contained; it is not
an independent external replication."""
import csv
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EST = HERE.parent / "between_repeat_phi_v3.py"
rng = random.Random(7)


def toy(path, phi_true):
    """20 cells x 3 repeats x 8 rows; phi_true 1.0 = binomial, 2.5 = Beta-binomial between repeats."""
    rows = []
    for c in range(20):
        p = rng.uniform(0.3, 0.7)
        for r in range(3):
            if phi_true > 1.0:
                rho = (phi_true - 1) / 7
                s = (1 - rho) / rho
                pr = rng.betavariate(p * s, (1 - p) * s)
            else:
                pr = p
            rows += [("cell_%02d" % c, "r%d" % r, 1 if rng.random() < pr else 0) for _ in range(8)]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["cell", "repeat", "correct"])
        w.writerows(rows)


toy(HERE / "toy_binomial.csv", 1.0)
toy(HERE / "toy_overdispersed.csv", 2.5)
(HERE / "malformed_bad_value.csv").write_text(
    "cell,repeat,correct\na,r0,1\na,r0,0\na,r1,1\na,r1,maybe\n", encoding="utf-8")
(HERE / "malformed_ragged_row.csv").write_text(
    "cell,repeat,correct\na,r0,1\na,r0,0,extra\na,r1,1\na,r1,0\n", encoding="utf-8")

out = []
for name in ("toy_binomial.csv", "toy_overdispersed.csv", "malformed_bad_value.csv", "malformed_ragged_row.csv"):
    p = subprocess.run([sys.executable, str(EST), str(HERE / name)], capture_output=True, text=True)
    out.append("## %s (exit %d)" % (name, p.returncode))
    out += [ln.rstrip() for ln in (p.stdout + p.stderr).splitlines() if ln.strip()]
got = "\n".join(out) + "\n"
exp_path = HERE / "EXPECTED_OUTPUT.txt"
if len(sys.argv) > 1 and sys.argv[1] == "--write-expected":
    exp_path.write_text(got, encoding="utf-8", newline="\n")
    print(got)
    print("wrote EXPECTED_OUTPUT.txt")
    sys.exit(0)
exp = exp_path.read_text(encoding="utf-8")
print(got)
print("EXAMPLES", "MATCH" if got == exp else "MISMATCH")
sys.exit(0 if got == exp else 1)
