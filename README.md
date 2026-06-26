# Daily Basket — Supplier-Claims Reconciliation Agent

> FDE trial deliverable. An agent that tells Daily Basket's Finance Director **how much suppliers owe them vs. how much they've recovered** — a question they could not answer before — and produces a human-gated, fully auditable claim pack behind every euro.

## The headline (Q1 2026, live engine output)

| Metric | Value |
|---|--:|
| **€ owed** (justified, de-duplicated) | **€6,203** |
| € recovered to date | €0 |
| **Recovery rate** | **0%** |
| **Missed** — should-claim, never logged | **€4,628** (3 claims) |
| Logged-correct — already on it | €1,125 |
| **Over-claim risk** — real, but logged twice | **€450** |
| Annualized run-rate (×4, seasonality caveat) | **€24,812** |

The €4,628 missed = Riverside damaged goods **€1,080** + Northgate volume rebate **€1,548** + Sunrise promo funding **€2,000** — exactly the rebate/credit money the manual process never checked.

## The thesis

**Don't automate the spreadsheet — replace it as the source of truth.** The tracker is the failure mode: single-owner (stops when Jenny is out), holds errors *and omissions*, and money that should have been claimed was never logged at all. The agent **derives** the claims that *should* exist from the ERP exports (PO ↔ Goods Receipt ↔ Invoice) + contracts, then uses the tracker only as a **reconciliation target** → buckets into **missed / logged-correct / over-claimed / not-substantiable**.

It is built to be trusted by a Finance Director: every € is transparent line-math, not opaque inference. It refuses to fabricate — the dairy "hero" claim a human abandoned proves to be **€0** once units are normalized, and Sweet Treats is left **unclaimable** because there is no goods receipt.

## Run it

```bash
python3 -m agent.run                 # full reconciliation report (read-only)
python3 -m agent.run --json          # machine-readable roll-up + claim packs
python3 tests/test_acceptance.py     # 13/13 acceptance criteria

# the only write — human-gated, idempotent, value-capped, stubbed for demo:
python3 -m agent.run --approve "SUP-001:Q1-2026|rebate" --approver "Mark Bryant"
python3 -m agent.run --submit
```

Python 3 stdlib only — no dependencies, deterministic, runs on any machine. Each run writes a joinable trace + audit record to `out/`.

## The three traps the agent gets right

1. **UoM normalization** — Meadowvale Dairy quotes per case (12 units/case). A naive compare reports a phantom €99k gap; normalized, INV-2003 reconciles *exactly* to PO-1003 = €9,000 → **no claim**. This is why Jenny "couldn't get the numbers to line up."
2. **No evidence, no claim** — Sweet Treats has no goods-receipt row; the shortage is unprovable, so the agent routes it to a human instead of inventing a claim.
3. **Duplicate detection** — Prime Cuts' real €450 overcharge was logged twice (CLM-004 + CLM-006, different owners/spelling); the agent flags the pair so Daily Basket doesn't chase — or get paid — twice.

## Deliverables map

| Deliverable | File |
|---|---|
| **Project Brief** (outcome + €-locked success) | [`PROJECT-BRIEF.md`](./PROJECT-BRIEF.md) |
| **Shipped agent** (working, tested) | [`agent/`](./agent/) · [`agent/README.md`](./agent/README.md) |
| **Spec** (source of truth, build plan) | [`SPEC.md`](./SPEC.md) |
| **Proof pack** (before/after, quantified) | [`PROOF-PACK.md`](./PROOF-PACK.md) |
| **Reusable asset** (portable recovery pattern) | [`prep/reusable-asset-claims-recovery-runbook.md`](./prep/reusable-asset-claims-recovery-runbook.md) |
| **Case study** (5 bullets) | [`CASE-STUDY.md`](./CASE-STUDY.md) |
| **Duvo agent design** (AOP, platform-native) | [`aop/`](./aop/) |
| Acceptance tests | [`tests/test_acceptance.py`](./tests/test_acceptance.py) |
| Scenario data (read-only) | [`data/`](./data/) |

## Repo layout

```
agent/      deterministic reconciliation engine (the shipped agent)
aop/        Duvo-platform-native agent design (AOP + provisioning payload)
data/       scenario CSVs + email thread (read-only inputs)
prep/       discovery questions, strategy, reusable asset
tests/      acceptance criteria (13/13 green)
out/        per-run trace + audit records
runbook/    the FDE Field Kit method this build follows
```

## Guardrails

Read-only on ERP / contracts / tracker · the **only write** is a human-gated, idempotent (`po_id|claim_type`), value-capped claim submission · transparent arithmetic · explicit UoM normalization · Q1-only (Q4 row excluded) · deterministic demo · every run observable via trace + audit.
