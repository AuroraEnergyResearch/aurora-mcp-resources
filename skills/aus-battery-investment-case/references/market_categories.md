# NEM market -> Aurora chart category mapping

Flexplorer's `investment_case` CSV export has one row per (Year, asset, market,
direction) with a `cashflow` column. The raw `market` values are granular.
Aurora's own AUS charts group them into **three** buckets:

| Chart category   | What it covers (per Aurora's own footnotes) |
|-------------------|----------------------------------------------|
| Energy revenue    | Wholesale arbitrage revenue **and** FCAS utilisation (spot-price) payments. This is the dominant bucket in every state — Aurora's own commentary describes wholesale arbitrage as the primary driver of BESS gross margin, with ancillary services secondary. |
| Regulation FCAS   | Capacity payments only (Regulation Raise + Regulation Lower services). Does not include the utilisation/spot component — that's already folded into Energy revenue above. |
| Contingency FCAS  | Capacity payments only (Contingency Raise 1sec/6sec/60sec/5min + Contingency Lower services). Same utilisation-vs-capacity split as Regulation FCAS. |

**This mapping is inferred from Aurora's published chart legends and
footnotes, not from a confirmed pull of the raw Flexplorer `market` string
list for the NEM region.** It has not been verified against a live API
response. Before running a real pull:

1. Call `flexplorer_get_investment_case_options(...)` for a NEM investment
   case and inspect `metadata.markets`.
2. Match each raw string to one of the three buckets above using the same
   logic Aurora applies (spot/utilisation cashflows -> Energy revenue;
   FCAS capacity-payment cashflows, split by Regulation vs Contingency
   sub-market -> the respective FCAS bucket).
3. Update this table with the confirmed raw strings once seen — list the
   exact strings you find (e.g. `Storage Wholesale discharge`) rather than
   leaving the mapping description generic.

If a `Project Total` or similarly-named redundant total row appears in the
export, ignore it and recompute totals by summing the buckets above so the
number is auditable.

`direction` is informational only (charge vs discharge) — cashflow sign
should already be correct (charging costs negative, discharge/capacity
revenue positive), so sum `cashflow` grouped by (Year, category). Don't
double-count by also filtering on direction.

## Important nuances for the NEM

- There is no standalone "Capacity Market" bucket in the standard NEM
  cases — the NEM is an energy-only market (see the report's market
  overview), so there's no capacity-market cashflow to bucket. (Government
  underwriting schemes like the CIS or SA FERM affect deal structuring and
  revenue certainty, not the per-case Flexplorer cashflow categories.)
- There is no "Network Charges" bucket shown in Aurora's AUS standard
  investment case charts. If the raw Flexplorer export for the NEM does
  expose network-charge-style cashflows (e.g. MLF, congestion, or similar
  location-value line items — see the co-located NPV waterfall example in
  the report's appendix, which does break out MLF/TGC/LGC/causer-pays
  items), treat that as a fourth bucket specific to whichever export you're
  looking at, and confirm with the client whether to fold it into Energy
  revenue or show it separately, rather than assuming a convention.
- This mapping is specific to the NEM (region code TBD — see SKILL.md
  step 2). Other Flexplorer regions may expose a different market
  taxonomy entirely; always re-check
  `flexplorer_get_investment_case_options().metadata.markets` before
  reusing any region's category mapping elsewhere.
