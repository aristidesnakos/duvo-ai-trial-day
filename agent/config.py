"""Period definition and small shared helpers. No magic numbers in the logic."""
from __future__ import annotations

import re
from datetime import date

# Period under reconciliation. Q1 2026 is closed as of early April 2026.
PERIOD_LABEL = "Q1-2026"
PERIOD_START = date(2026, 1, 1)
PERIOD_END = date(2026, 3, 31)

# Normalized tracker status vocabulary.
STATUS_OPEN = "OPEN"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_PAID = "PAID"

_STATUS_MAP = {
    "open": STATUS_OPEN,
    "in progress": STATUS_IN_PROGRESS,
    "wip": STATUS_IN_PROGRESS,
    "pending": STATUS_IN_PROGRESS,
    "paid": STATUS_PAID,
}


def normalize_status(raw: str) -> str:
    """Collapse the inconsistent tracker statuses to a 3-value vocabulary."""
    return _STATUS_MAP.get((raw or "").strip().lower(), STATUS_OPEN)


def parse_date(raw: str):
    """Parse YYYY-MM-DD or DD/MM/YYYY (CLM-003 uses the latter). None if blank."""
    raw = (raw or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            from datetime import datetime
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def in_period(d) -> bool:
    return d is not None and PERIOD_START <= d <= PERIOD_END


def units_per_case_from_note(note: str) -> int:
    """Extract pack size from a contract note, e.g. '12 units/case' -> 12.

    Generic on purpose: SUP-003 is the known trap, but the SPEC assumes other
    UoM traps may exist, so we read the rule from the contract rather than
    hard-coding a single supplier.
    """
    m = re.search(r"(\d+)\s*units?\s*/\s*case", note or "", re.IGNORECASE)
    return int(m.group(1)) if m else 1


def first_int(text: str):
    """First integer in a free-text note (fallback only)."""
    m = re.search(r"\d+", text or "")
    return int(m.group(0)) if m else None


def damage_qty_from_note(note: str, uom: str):
    """Extract a damaged quantity from GRN free text, ANCHORED to context.

    Returns (qty, confidence). A bare first-integer grab is dangerous — a note
    like "delivered 2026, 120 damaged" would yield 2026. So we prefer a number
    bound to the unit token (e.g. "120 cases") or to a damage keyword, and only
    fall back to the first integer at LOW confidence so the caller can flag it.
    """
    if not note:
        return None, "low"
    # 1) number immediately followed by the GRN's unit (e.g. "120 cases").
    m = re.search(rf"(\d+)\s*{re.escape(uom)}s?\b", note, re.IGNORECASE)
    if m:
        return int(m.group(1)), "high"
    # 2) number adjacent to a damage keyword.
    m = re.search(r"(\d+)[^\d]{0,12}(?:leak|crush|damag|broken|spoil|smash)",
                  note, re.IGNORECASE)
    if m:
        return int(m.group(1)), "medium"
    n = first_int(note)
    return (n, "low") if n is not None else (None, "low")


def eur(x: float) -> str:
    return f"€{x:,.2f}"
