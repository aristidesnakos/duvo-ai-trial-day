"""compute_entitlements — per-supplier volume rebate + promo funding owed.

Earned-but-unclaimed money is where the operator bet the value was. We test it
honestly: a rebate is only owed if cumulative Q1 spend actually crosses the
contract threshold (most suppliers don't), and promo funding is owed whenever
the contract states a per-quarter amount.
"""
from __future__ import annotations

from typing import List

from . import config
from .loader import PeriodData
from .models import DerivedClaim


def compute_entitlements(data: PeriodData) -> List[DerivedClaim]:
    claims: List[DerivedClaim] = []

    # Cumulative Q1 spend per supplier (PO totals; basis = "cumulative net spend").
    spend = {}
    pos_by_supplier = {}
    for po in data.purchase_orders:
        spend[po.supplier_id] = spend.get(po.supplier_id, 0.0) + po.po_total_eur
        pos_by_supplier.setdefault(po.supplier_id, []).append(po.po_id)

    for c in data.contracts:
        s = spend.get(c.supplier_id, 0.0)
        po_list = pos_by_supplier.get(c.supplier_id, [])

        # --- Volume rebate ---
        if c.volume_bonus_threshold_eur_qtr > 0 and c.volume_bonus_pct > 0:
            crossed = s >= c.volume_bonus_threshold_eur_qtr
            if crossed:
                amount = round(s * c.volume_bonus_pct / 100.0, 2)
                claims.append(DerivedClaim(
                    po_id=None, supplier_id=c.supplier_id, supplier_name=c.supplier_name,
                    claim_type="rebate", eur_amount=amount,
                    line_math=(f"Q1 spend {config.eur(s)} ≥ threshold "
                               f"{config.eur(c.volume_bonus_threshold_eur_qtr)} → "
                               f"{c.volume_bonus_pct:g}% × {config.eur(s)} = {config.eur(amount)}"),
                    evidence={"pos_summed": po_list, "q1_spend_eur": round(s, 2),
                              "threshold_eur": c.volume_bonus_threshold_eur_qtr,
                              "pct": c.volume_bonus_pct},
                    uom_normalized=False, confidence="high", period=data.period,
                ))
            else:
                gap = c.volume_bonus_threshold_eur_qtr - s
                # Not a claim — recorded as a transparent near-miss (€0), for the
                # procurement-timing conversation, never raised as money owed.
                claims.append(DerivedClaim(
                    po_id=None, supplier_id=c.supplier_id, supplier_name=c.supplier_name,
                    claim_type="rebate_below_threshold", eur_amount=0.0,
                    line_math=(f"Q1 spend {config.eur(s)} < threshold "
                               f"{config.eur(c.volume_bonus_threshold_eur_qtr)} "
                               f"(short by {config.eur(gap)}) → no rebate earned"),
                    evidence={"pos_summed": po_list, "q1_spend_eur": round(s, 2),
                              "threshold_eur": c.volume_bonus_threshold_eur_qtr,
                              "shortfall_eur": round(gap, 2)},
                    uom_normalized=False, confidence="high", period=data.period,
                ))

        # --- Promo funding (per-quarter co-funding stated in the contract) ---
        # The contract must be active across the period for a full-quarter amount
        # to be safely claimable. If it lapses or starts mid-period, the full €/qtr
        # is an assumption (pro-rate or confirm), so we drop confidence and caveat
        # the line-math rather than overstate certainty. (Reusable-asset §6.)
        if c.promo_funding_eur_qtr > 0:
            c_start = config.parse_date(c.contract_start)
            c_end = config.parse_date(c.contract_end)
            lapses_early = c_end is not None and c_end < config.PERIOD_END
            starts_late = c_start is not None and c_start > config.PERIOD_START
            partial_period = lapses_early or starts_late
            if partial_period:
                confidence = "medium"
                caveat = (f" — ⚠ contract active {c.contract_start}→{c.contract_end}, "
                          f"NOT the full period ({config.PERIOD_LABEL}); full-quarter amount "
                          f"assumed — pro-rate or confirm before quoting")
            else:
                confidence = "high"
                caveat = ""
            claims.append(DerivedClaim(
                po_id=None, supplier_id=c.supplier_id, supplier_name=c.supplier_name,
                claim_type="promo", eur_amount=round(c.promo_funding_eur_qtr, 2),
                line_math=(f"Contract promo co-funding {config.eur(c.promo_funding_eur_qtr)}/qtr "
                           f"for {data.period}{caveat}"),
                evidence={"contract_note": c.notes,
                          "promo_funding_eur_qtr": c.promo_funding_eur_qtr,
                          "contract_start": c.contract_start, "contract_end": c.contract_end,
                          "contract_covers_full_period": not partial_period},
                uom_normalized=False, confidence=confidence, period=data.period,
            ))

    return claims
