# Flexplorer market -> Aurora chart category mapping

Flexplorer's `investment_case` CSV export has one row per (Year, asset, market,
direction) with a `cashflow` column. The raw `market` values are granular
(20+ distinct strings). Aurora's own charts group them into four buckets.
Use this exact mapping so charts match Aurora's convention:

| Chart category      | Raw `market` values (sum cashflow across all of these) |
|----------------------|----------------------------------------------------------|
| Energy Trading       | `Storage Day-Ahead charge`, `Storage Day-Ahead discharge`, `Storage Intraday charge`, `Storage Intraday discharge`, `Storage Balancing Mechanism Energy charge`, `Storage Balancing Mechanism Energy discharge`, `Storage Balancing Mechanism Location charge`, `Storage Balancing Mechanism Location discharge`, `RES-to-storage`, `RES Wholesale`, `Storage-from-RES` |
| Frequency Response / Ancillary Services | `Storage Dynamic Containment`, `Storage Dynamic Moderation`, `Storage Dynamic Regulation`, `Storage Balancing Reserve`, `Storage Quick Reserve` |
| Capacity Market      | `Storage Capacity Market` |
| Network Charges      | `Project TNUoS generation wider tariff`, `Project Triads (EET)`, `Project GDUoS capacity`, `Project GDUoS unit` |

Ignore the `Project Total` market if present — it's a redundant total row in
some exports; always recompute totals yourself by summing the four buckets
above so the number is auditable.

`direction` is informational only (charge vs discharge) — cashflow sign is
already correct (charging costs are negative, discharge revenue positive),
so just sum `cashflow` grouped by (Year, category). Don't double-count by
also filtering on direction.

Co-located (solar+battery) exports add a `Solar Gross Margin` style series
from the RES asset's own Day-Ahead sales — keep this as its own category
("Solar Gross Margin") rather than folding into Energy Trading, matching
Aurora's co-located chart legend (page 219).

This mapping is specific to GB (`gbr`). Other Flexplorer regions may expose
a different market list — call `flexplorer_get_investment_case_options` and
check `metadata.markets` before assuming this mapping applies.
