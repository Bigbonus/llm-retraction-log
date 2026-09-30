# -*- coding: utf-8 -*-
"""Write P1C_RUN_MANIFEST_V1.json: sha256 of the runner, the estimator and both protocol documents,
plus the frozen settings, before the outcome run starts. Refuses to overwrite an existing manifest."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
H = Path(r"G:\chappy_ai_storage\handoff")
OUT = HERE / "P1C_RUN_MANIFEST_V1.json"
if OUT.exists():
    sys.exit("manifest exists, not overwriting")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


m = {"id": "SUB70_P1C_RUN_MANIFEST_V1",
     "runner": "p1c_run_v1.py", "runner_sha256": sha(HERE / "p1c_run_v1.py"),
     "estimator": "between_repeat_phi_v3.py", "estimator_sha256": sha(HERE / "between_repeat_phi_v3.py"),
     "protocol_draft": "P1C_PROTOCOL_DRAFT_V1.md", "protocol_draft_sha256": sha(HERE / "P1C_PROTOCOL_DRAFT_V1.md"),
     "protocol_addendum": "SUB70_V5_REVIEW_P1C_FREEZE_ADDENDUM_V1.md",
     "protocol_addendum_sha256": sha(H / "SUB70_V5_REVIEW_P1C_FREEZE_ADDENDUM_V1.md"),
     "settings": {"families": ["S1", "S2:1.10", "S2:1.25", "S2:1.50", "S3"], "C": [20, 60, 166], "m": [4, 8, 12],
                  "R": 4, "N": 100, "NPERM": 1000, "base_seed": 20260930, "dataset_seed": "base+100000*j+k",
                  "perm_seed": "dataset_seed+1000000000", "reject": "p<0.05", "budget_min": 120, "workers": 1}}
OUT.write_text(json.dumps(m, indent=1), encoding="utf-8", newline="\n")
for k in ("runner_sha256", "estimator_sha256", "protocol_draft_sha256", "protocol_addendum_sha256"):
    print(k, m[k][:12])
print("wrote", OUT.name, "sha", sha(OUT)[:12])
