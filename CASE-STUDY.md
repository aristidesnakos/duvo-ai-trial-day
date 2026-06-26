# Case Study — Daily Basket Supplier Claims Agent

> Duvo internal-publish style: one headline + 5 bullets. Numbers are live engine output, cross-verified.

**Headline:** Daily Basket couldn't say how much suppliers owed them — we shipped an agent that computes **€6,203 owed, a 0% recovery rate, and €4,628 in money the old process never logged**, with a human-gated claim pack behind every euro.

- **Problem:** Daily Basket (~€180M GMV online grocer) is owed money by suppliers — short/damaged deliveries, prices above contract, earned rebates & promo funding — but the claims process lived in one person's spreadsheet, so money that was never logged was never recovered.
- **Symptoms:** Finance had no answer to the Finance Director's question *"how much are we recovering vs. how much is owed?"*; claims were reactive (*"I catch what I catch"*); rebate thresholds for flour/drinks/packaging/dairy were almost never checked; and when the owner was out sick for two weeks, credit windows nearly closed.
- **Approach:** An agent **derives** the claims that should exist from ERP exports (PO ↔ Goods Receipt ↔ Invoice) + contracts — normalizing the per-case UoM that defeated a human — reconciles them against the tracker into **missed / logged-correct / over-claimed / not-claimable**, and produces a human-gated, idempotent claim pack with € and evidence. Deterministic, transparent arithmetic; runs end-to-end without Jenny.
- **Proof (€):** €6,203 owed · 0% recovery rate · **€4,628 missed** (Riverside damage €1,080 + Northgate rebate €1,548 + Sunrise promo €2,000) · **€450 duplicate** caught (Prime Cuts logged twice) · annualized ≈ €24,812/yr. 11/11 acceptance criteria pass.
- **What makes it trustworthy:** it doesn't fabricate — the "hero" dairy claim is proven to be **€0** once units are normalized (so they stop chasing it), Sweet Treats is left **unclaimable** because there's no goods receipt, and only the **one** rebate supplier that actually crossed its threshold is claimed. The agent shows a Finance Director where the money *isn't* as confidently as where it is.
