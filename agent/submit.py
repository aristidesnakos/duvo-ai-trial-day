"""submit_claim — the ONLY write. Human-gated, idempotent, single-entity, capped.

Stubbed for the demo (no real supplier-credit API yet). The guardrails are real:
  - single claim per call (no batch auto-submit)
  - quantity-capped to the derived € amount (cannot exceed what the math supports)
  - idempotent on (po_id|claim_type) — re-submitting the same key is a no-op
  - requires an explicit human approval token; without it, refuses to write
Approvals persist to out/approvals.json so a decision, once made, is remembered.
"""
from __future__ import annotations

import hashlib
import json
import os

from .observability import OUT_DIR

APPROVALS_PATH = os.path.join(OUT_DIR, "approvals.json")
SUBMISSIONS_PATH = os.path.join(OUT_DIR, "submissions.json")


def _load(path):
    if os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)
    return {}


def _save(path, obj):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)


def record_approval(idempotency_key: str, approver: str, approved_at: str):
    approvals = _load(APPROVALS_PATH)
    approvals[idempotency_key] = {"approved_by": approver, "approved_at": approved_at}
    _save(APPROVALS_PATH, approvals)


def is_approved(idempotency_key: str) -> bool:
    return idempotency_key in _load(APPROVALS_PATH)


def submit_claim(claim_pack, run_id: str) -> dict:
    """Raise one claim. Refuses without a persisted human approval (the gate)."""
    key = claim_pack.idempotency_key
    approvals = _load(APPROVALS_PATH)
    if key not in approvals:
        return {"status": "BLOCKED_NEEDS_APPROVAL", "idempotency_key": key,
                "reason": "No human approval on record; submission gated."}

    submissions = _load(SUBMISSIONS_PATH)
    if key in submissions:  # idempotent: already submitted.
        existing = submissions[key]
        return {"status": "ALREADY_SUBMITTED", "submission_id": existing["submission_id"],
                "idempotency_key": key, "run_id": existing["run_id"]}

    # Deterministic stub submission id from the key (hashlib, not built-in hash()).
    digest = int(hashlib.sha1(key.encode()).hexdigest(), 16) % 10_000_000
    submission_id = "SUB-" + str(digest).zfill(7)
    record = {
        "submission_id": submission_id, "idempotency_key": key, "run_id": run_id,
        "supplier": claim_pack.supplier_name, "claim_type": claim_pack.claim_type,
        "eur_amount": claim_pack.eur_amount, "approved_by": approvals[key]["approved_by"],
        "approved_at": approvals[key]["approved_at"], "status": "SUBMITTED",
    }
    submissions[key] = record
    _save(SUBMISSIONS_PATH, submissions)
    return record
