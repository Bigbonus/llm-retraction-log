# -*- coding: utf-8 -*-
"""P1-c outcome run, exactly as frozen by SUB70_V5_REVIEW_P1C_FREEZE_ADDENDUM_V1 (af5b78320ad7),
which overrides P1C_PROTOCOL_DRAFT_V1.md (86638721c85b) where they conflict.

Families in order: S1, S2(1.10), S2(1.25), S2(1.50), S3. Within a family: C in [20, 60, 166] then
m in [4, 8, 12]. R = 4. Point index j = 0..44. N = 100 datasets per point, k = 0..99.
dataset seed = 20260930 + 100000*j + k; permutation RNG seed = dataset seed + 1000000000.
NPERM = 1000. p = (1 + #permuted >= observed) / 1001 (between_repeat_phi_v3.permutation_p);
reject iff p < 0.05. Eligibility as the estimator fixes it; a dataset with no usable cell is
counted separately, never as a non-rejection.

Generators (p_c ~ Uniform(0.2, 0.8) once per cell; conditional on p_c):
  S1  y ~ Bernoulli(p_c) i.i.d.
  S2  per repeat p_{c,r} ~ Beta(a, b), mean p_c, a + b = (1 - rho)/rho, rho = (phi - 1)/(m - 1);
      y ~ Bernoulli(p_{c,r}) within the repeat
  S3  m items per cell, d_i ~ Beta(4 p_c, 4 (1 - p_c)) once per item, reused in all R repeats;
      y_{i,r} ~ Bernoulli(d_i). Stress test: the permutation is the estimator's unrestricted
      within-cell shuffle, kept on purpose; its rejection rate is neither FPR nor power.

Budget: one worker; wall-clock checked between datasets; cooperative stop at 120 min, completed
results kept, run marked incomplete. Results persisted after every point; elapsed time recorded.
Output: P1C_RESULTS_V1.json (next to this file). Run once."""
import hashlib
import json
import math
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import between_repeat_phi_v3 as M  # noqa: E402

BASE = 20260930
N = 100
NPERM = 1000
R = 4
CS = (20, 60, 166)
MS = (4, 8, 12)
FAMILIES = (("S1", None), ("S2", 1.10), ("S2", 1.25), ("S2", 1.50), ("S3", None))
BUDGET_S = 120 * 60
OUT = HERE / "P1C_RESULTS_V1.json"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def gen(family, phi, C, m, rng):
    cells = defaultdict(list)
    for c in range(C):
        p = rng.uniform(0.2, 0.8)
        key = "c%d" % c
        if family == "S1":
            for r in range(R):
                cells[key].extend((str(r), 1 if rng.random() < p else 0) for _ in range(m))
        elif family == "S2":
            rho = (phi - 1) / (m - 1)
            s = (1 - rho) / rho
            for r in range(R):
                pr = rng.betavariate(p * s, (1 - p) * s)
                cells[key].extend((str(r), 1 if rng.random() < pr else 0) for _ in range(m))
        else:  # S3
            d = [rng.betavariate(4 * p, 4 * (1 - p)) for _ in range(m)]
            for r in range(R):
                cells[key].extend((str(r), 1 if rng.random() < d[i] else 0) for i in range(m))
    return cells


def wilson(x, n, z=1.959964):
    if n == 0:
        return None
    ph = x / n
    den = 1 + z * z / n
    cen = (ph + z * z / (2 * n)) / den
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return [round(cen - half, 4), round(cen + half, 4)]


def main():
    t_start = time.time()
    manifest = json.loads((HERE / "P1C_RUN_MANIFEST_V1.json").read_text(encoding="utf-8"))
    assert manifest["runner_sha256"] == sha(__file__), "runner changed after manifest"
    assert manifest["estimator_sha256"] == sha(HERE / "between_repeat_phi_v3.py"), "estimator changed"
    res = {"id": "SUB70_P1C_RESULTS_V1", "manifest": manifest, "status": "running", "points": [],
           "started_epoch": t_start}
    j = 0
    stopped = False
    for fam, phi in FAMILIES:
        for C in CS:
            for m in MS:
                pt = {"j": j, "family": fam, "phi_true": phi, "C": C, "m": m, "R": R, "N": N,
                      "datasets_done": 0, "no_usable_cell": 0, "tested": 0, "rejected": 0,
                      "excluded_cells_total": 0, "phi_hat": [], "p": []}
                for k in range(N):
                    if time.time() - t_start > BUDGET_S:
                        stopped = True
                        break
                    ds = BASE + 100000 * j + k
                    cells = gen(fam, phi, C, m, random.Random(ds))
                    used, why = M.split_usable(cells)
                    pt["excluded_cells_total"] += sum(why.values())
                    pt["datasets_done"] += 1
                    if not used:
                        pt["no_usable_cell"] += 1
                        continue
                    X2, DF = M.phi(used)
                    p, _ = M.permutation_p(used, X2, random.Random(ds + 1000000000), nperm=NPERM)
                    pt["tested"] += 1
                    pt["rejected"] += p < 0.05
                    pt["phi_hat"].append(round(X2 / DF, 4))
                    pt["p"].append(round(p, 4))
                n = pt["tested"]
                pt["reject_rate"] = round(pt["rejected"] / n, 4) if n else None
                pt["wilson95"] = wilson(pt["rejected"], n)
                pt["mc_se"] = round(math.sqrt(pt["reject_rate"] * (1 - pt["reject_rate"]) / n), 4) if n and pt["reject_rate"] not in (0.0, 1.0) else None
                pt["complete"] = pt["datasets_done"] == N
                res["points"].append(pt)
                res["elapsed_s"] = round(time.time() - t_start, 1)
                OUT.write_text(json.dumps(res, indent=1), encoding="utf-8", newline="\n")
                print("j %2d %s phi %s C %3d m %2d  tested %3d rejected %3d  rate %s  no-usable %d  %.0fs"
                      % (j, fam, phi, C, m, n, pt["rejected"], pt["reject_rate"], pt["no_usable_cell"], time.time() - t_start), flush=True)
                j += 1
                if stopped:
                    break
            if stopped:
                break
        if stopped:
            break
    res["status"] = "incomplete_budget" if stopped else "complete"
    res["elapsed_s"] = round(time.time() - t_start, 1)
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8", newline="\n")
    print("status", res["status"], "elapsed %.0fs" % res["elapsed_s"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
