"""run_id + trace (engineer) and audit (business) records, joinable by run_id.

run_id is DETERMINISTIC (content hash of the inputs), so the same data yields
the same run_id every time — a demo requirement and an audit convenience. No
secrets are ever written.
"""
from __future__ import annotations

import hashlib
import json
import os

from .models import to_jsonable

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "out")


def make_run_id(data) -> str:
    fingerprint = "|".join([
        data.period,
        str(len(data.purchase_orders)),
        str(len(data.goods_receipts)),
        str(len(data.invoices)),
        str(len(data.contracts)),
        str(len(data.tracker)),
    ])
    digest = hashlib.sha1(fingerprint.encode()).hexdigest()[:8]
    return f"run-{data.period}-{digest}"


def write_records(run_id: str, trace: dict, audit: dict):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, f"{run_id}.trace.json"), "w") as fh:
        json.dump(to_jsonable(trace), fh, indent=2, ensure_ascii=False)
    with open(os.path.join(OUT_DIR, f"{run_id}.audit.json"), "w") as fh:
        json.dump(to_jsonable(audit), fh, indent=2, ensure_ascii=False)
    return OUT_DIR
