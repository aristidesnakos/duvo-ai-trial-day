# email_thread.pdf — intelligence (claims@dailybasket.com, exported 31 Mar 2026)

Three messages, Jenny ⇄ Paula, the night before Jenny goes on leave. This is the discovery session in miniature — it confirms the thesis and names the exact cases to verify in the data.

## Strategic confirmations (use these verbatim in the room)

- **Mark's real question = the success metric:** *"how much are we actually recovering vs. how much is owed to us?"* Paula had **no answer**. → Frame success as a **recovery rate: € recovered ÷ € owed**, and our agent is the thing that can finally compute the denominator.
- **The thesis, in their words:** *"We don't track what we should have claimed, only what we happened to chase."* → The value is the **un-claimed** money, not digitizing the sheet.
- **Key-person risk is real and costly:** Jenny out sick in Feb → *"nobody touched this sheet for two weeks and a couple of credit windows nearly closed on us."* → Resilience (runs without Jenny) has hard € consequences (missed credit windows).
- **Where the big money is (Jenny's own bet):** *"the suppliers with rebate deals — flour, the drinks one, packaging, dairy — I almost never check whether we've crossed the threshold. That's where I'd bet the real money is, and it's exactly the part I never get to."* → **Rebate entitlements are the headline upside.**
- **The naive ask, to push back on:** *"Let's just automate the sheet or something. Anything."*
- **How claims get triggered today (the gap):** *"I only chase a claim when a supplier emails us or something looks obviously wrong... I catch what I catch."* → Reactive, not systematic.

## Named cases to verify against the CSVs (built-in test set)

| # | Supplier | Jenny's note | Expected finding in data | Bucket |
|---|---|---|---|---|
| 1 | **Greenfield Farm** | Short delivery, tomatoes 150 kg, still open; GRN sent, no credit note | PO qty > GR qty by 150 kg; claim justified, **open** | logged-correct (open) |
| 2 | **Sunrise Bakery** | Rolls overcharge **€750**, supplier stalling | Invoice price > contract price → price-gap claim ≈ €750 | logged-correct (disputed) |
| 3 | **Prime Cuts Butchers** | Meat claim *"logged in a rush, feeling it's in there twice"* | **Duplicate row** in tracker → **over-claim risk** | over-claimed / cleanup |
| 4 | **Meadowvale Dairy** (SUP-003) | *"couldn't get the numbers to line up, ran out of time"* | **The per-case UoM trap** (12 units/case). Likely a **real claim she missed** because units didn't reconcile | **missed** (flagship) |
| 5 | **Sweet Treats** | Gummy bears; supplier says delivered, *"can't find paperwork our side"* | No/short GR; **no evidence to substantiate** → not claimable, or supplier is right | not claimable (judgment) |

### Why #4 (Meadowvale Dairy) is the demo's hero moment
Jenny literally couldn't make dairy reconcile and gave up. The Data README warns SUP-003 quotes **per case (12 units/case)**. The agent that normalizes UoM will surface a claim a human abandoned — the cleanest possible illustration of "money never logged at all." Lead the demo with this.

### Rebate suppliers to compute entitlements for
Flour, drinks, packaging, dairy (per Jenny). Cross-check `supplier_contracts.csv` for rebate thresholds and Q1 volumes — **this is where she bets the real money is, and she never checks it.**

## Implications for the build

- The **reconciliation output buckets** map directly onto these cases: missed (dairy + rebates), logged-correct (Greenfield, Sunrise), over-claimed (Prime Cuts duplicate), not-claimable (Sweet Treats).
- Add an explicit **"evidence sufficiency"** check: Sweet Treats shows a claim can't be raised without a GR — don't fabricate claims the data can't defend.
- The **proof pack** writes itself: "€ owed vs € recovered" + the dairy claim Jenny abandoned + the Prime Cuts double-count we caught.
