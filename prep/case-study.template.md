# Case Study — Daily Basket Supplier Claims Agent

> Duvo internal-publish style: one headline + exactly 5 bullets. Fill `[€X]`-style placeholders once the CSVs are analyzed and the numbers are agreed on the day. Keep it crisp and publishable internally.

**Headline:** Daily Basket couldn't say how much suppliers owed them — we shipped an agent that computes €[X] owed, a [Z]% recovery rate, and €[A] in money the old process never caught.

- **Problem:** Daily Basket (~€180M GMV online grocer) is owed money by suppliers — short/damaged deliveries, prices above contract, earned rebates & promo funding — but the claims process lived in one person's spreadsheet, so money that was never logged was never recovered.
- **Symptoms:** Finance had no answer to the Finance Director's question *"how much are we recovering vs. how much is owed?"*; claims were reactive (*"I catch what I catch"*); rebate thresholds for flour/drinks/packaging/dairy were almost never checked; and when the owner was out sick for two weeks, credit windows nearly closed.
- **Before:** € owed was never computed, recovery rate was unanswerable, the un-claimed long tail was invisible, and the whole process stopped when one person was unavailable.
- **After:** An agent **derives** the claims that should exist from ERP exports (PO ↔ Goods Receipt ↔ Invoice) + contracts, reconciles them against the tracker into **missed / logged-correct / over-claimed**, produces a human-gated claim pack with € and evidence, and runs whether or not Jenny is in — including normalizing the per-case UoM that made one dairy claim impossible to reconcile by hand.
- **Proof (€):** €[X] owed · [Z]% recovery rate · €[A] missed money recovered (annualized run-rate ≈ €[E]/yr) — featuring the **Meadowvale Dairy** claim a human abandoned (€[F], surfaced via UoM normalization), a **Prime Cuts** duplicate caught (€[G] over-claim avoided), and **€[D]** in never-checked rebate entitlements.
