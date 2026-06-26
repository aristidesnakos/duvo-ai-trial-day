# SupplierLedger — the supplier's private books

This is each supplier's **own record** of what it shipped, billed, and agreed — the counterparty's
source of truth, kept on the far side of the boundary from Daily Basket's books. In the simulation
the **Supplier Simulator agent reads ONLY this tab plus the incoming Correspondence claim**. It never
sees our `GoodReceipts`, never sees the validated findings, never sees an answer key. When a claim
arrives it looks up its own row, compares our assertion to *its* figures, and decides on that basis:

- our number matches its row → **agree** (issue a credit note);
- its row says something different → **dispute** with its own figure;
- it has no record / no evidence → **deny** and ask us for proof;
- the underlying term has lapsed → offer a **partial** (pro-rated) credit;
- it owes the money but wants to verify internally first → **stall, then concede**.

Because the genuine money (Greenfield short, Sunrise rolls, Riverside damage, Prime Cuts overcharge,
Northgate rebate) is corroborated in the ledger, it stays recoverable. The instructive disagreements
(Meadowvale unit basis, Sweet Treats missing GRN, Sunrise promo lapse, Prime Cuts duplicate, EcoPack
under-threshold) are seeded as real divergences so the right outcome **emerges from the two datasets**,
not from a script. The `stance` column records the supplier's intended posture; the simulator should
derive it from the data, with `stance` as the design intent / fallback label.

## Seed CSV — `SupplierLedger` tab

```csv
supplier_slug,po_ref,sku,qty_they_shipped,unit_price_they_billed,unit_basis,their_terms_note,prior_credits,stance
northgate,PO-1001;PO-1014;PO-1022,FLR-001,4300,12.00,case,"Q1 net spend 24000+18000+9600 = 51600 EUR, over the 50000 EUR quarterly threshold; rebate 3% = 1548 EUR confirmed payable",0,agree_rebate
greenfield,PO-1002,VEG-014,850,2.50,kg,"Dispatch note shows 850 kg loaded; driver recorded 150 kg short on the delivery note; produce credited against shortage",0,agree_short
meadowvale,PO-1003,DRY-101,500,18.00,case,"Pricelist is per case of 12 units; 500 cases x 18.00 = 9000 EUR; their unit-price line of 1.50 is just 18.00/12, not an overcharge",0,refute_unit_basis
sunrise,PO-1004,BAK-220,5000,0.95,unit,"Agreed pricelist price is 0.80/unit; billed 0.95 in error; will check with finance before confirming, then concede 750 EUR overcharge",0,stall_then_concede
sunrise,PO-1004,PROMO-Q1,1,1333.00,quarter,"Promo co-funding 2000 EUR/qtr but our contract copy shows promo end 2026-02-28; lapsed mid-Q1, so only 2 of 3 months fundable = 1333 EUR pro-rated, not 2000",0,partial_promo
riverside,PO-1005,BEV-330,2000,9.00,case,"120 cases bottles leaking/crushed in transit; photos on file; transit damage credited at 120 x 9.00 = 1080 EUR",0,agree_damage
primecuts,PO-1006,MEA-410,1500,6.80,kg,"Pricelist is 6.50/kg; billed 6.80 in error; one 450 EUR overcharge line acknowledged. A second identical claim was already raised and credited - duplicate disputed",0,agree_once_dispute_duplicate
sweettreats,PO-1007,CON-510,8000,0.45,unit,"Dispatch record shows full 8000 units loaded and delivered; deny any shortage; ask grocer for receipt evidence (we hold none on our side either)",0,deny_delivered_full
ecopack,PO-1008;PO-1013;PO-1021,PKG-MIX,Q1,15000.00,case,"Q1 net spend 15000+7200+13500 = 35700 EUR, under the 60000 EUR quarterly threshold; no volume rebate due this quarter",0,refute_threshold
```

> **Notes on the seeded rows**
> - `northgate` / `ecopack` are rebate rows, not single shipments — `po_ref` lists the Q1 POs, `qty_they_shipped` carries an indicative aggregate (cases / N/A), and the threshold maths lives in `their_terms_note`. The decision is purely "Q1 net spend vs threshold".
> - `sunrise` has **two** rows: the rolls pricelist line (real overcharge, conceded after a stall) and a separate `PROMO-Q1` line (lapsed mid-quarter → pro-rated partial). Keeping them apart lets the simulator concede one and partial the other.
> - `prior_credits` is 0 everywhere in this seed; it exists so the ledger can later show a credit already issued (e.g. the Prime Cuts duplicate, if we want the "already raised" stance to point at a prior credit row).

## Claim-vs-ledger reconciliation matrix

| Supplier | Their stance | What our claim says | Does their data agree? | Resulting behavior |
|---|---|---|---|---|
| greenfield | `agree_short` | 150 kg short on PO-1002 → credit €375 | Yes — dispatch note also shows 850 kg, driver logged the shortage | **Credit €375** |
| sunrise (rolls) | `stall_then_concede` | Rolls billed €0.95 vs €0.80 → €750 overcharge | Yes — pricelist is €0.80; €0.95 was an error | **Stall on first contact, then credit €750** |
| sunrise (promo) | `partial_promo` | Promo co-funding €2,000 due for Q1 | Partly — promo ended 2026-02-28, lapsed mid-Q1 | **Partial: credit pro-rated ~€1,333, not €2,000** |
| riverside | `agree_damage` | 120 cases damaged → credit €1,080 | Yes — acknowledges 120 cases damaged in transit, photos on file | **Credit €1,080** |
| primecuts | `agree_once_dispute_duplicate` | Chicken overcharge €450 (two logged claims) | One €450 line yes; the second is the same claim | **Credit €450 once; dispute the duplicate ("already raised")** |
| meadowvale | `refute_unit_basis` | Milk price discrepancy (€1.50 vs €18.00) | No — pricelist is per case of 12; €1.50 = €18.00/12; totals match at €9,000 | **Dispute / refute: no credit, explains unit basis** |
| sweettreats | `deny_delivered_full` | Gummy bears short on PO-1007 | No — dispatch record shows full 8,000 units delivered | **Deny; ask for proof (we have none — GRN-3007 missing → stalemate)** |
| northgate | `agree_rebate` | Q1 volume rebate €1,548 (€51,600 ≥ €50k @ 3%) | Yes — their books show ~€51,600 Q1 net spend over threshold | **Confirm rebate €1,548 due** |
| ecopack | `refute_threshold` | (Potential) Q1 volume rebate | No — their books show ~€35,700 Q1 net spend, under €60k threshold | **Refute: no rebate due this quarter** |
