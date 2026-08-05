---
name: gb-battery-investment-case
description: Build an interactive GB battery storage investment-case artifact from Aurora Flexplorer data — revenue-by-market charts, cross-comparison (duration/location/scenario), and a client-editable NPV/IRR/payback waterfall that recommends which option makes the most cash. Use this whenever a client asks to compare battery durations (2hr/4hr/8hr), compare GB price zones or scenarios for storage, or wants "which battery makes the most money". Trigger even if they just say "run the investment case" or name a Flexplorer scenario, region, or duration without asking for a chart explicitly.
---

# GB battery investment case builder

Reproduces Aurora's standard battery investment-case chart types as a
live artifact — charts and numbers only, never Aurora's written
commentary. The client types in their own capex/opex/discount-rate
assumptions and the NPV/IRR ranking recomputes live.

Read `references/chart_types.md` for exact chart specs plus the canonical
CSS/structure to copy, `references/market_categories.md` for the
Flexplorer market groupings, and `references/finance_formulas.md` for the
JS to embed before writing any code. The full worked HTML example under
`references/examples/` is optional — only open it if you need the Chart.js
wiring in full; the style and panel order are already in `chart_types.md`.

## Guiding principle: ask, don't assume

This skill is a slow, expensive pipeline (multiple MCP calls, a data
pull, an artifact build) wrapped around a handful of decisions that are
genuinely the client's to make — which scenario is "official," which
durations matter, whether the ranking should even be built yet. Don't
front-load all of that into one round of questions and then disappear
into tool calls for two minutes. Check in at each decision point, and
show something (a table, a quick chart) before committing to the full
build. A client who's watched their comparison narrow step by step will
trust the final artifact more than one who's handed a finished dashboard
cold.

Concretely: never silently pick a scenario, a duration set, or a zone on
the client's behalf, even when one option is obviously the newest or most
common choice. Recommend it, explain why in one line, and let them
confirm or override with `ask_user_input_v0`. The only exception is when
the client already gave you the answer in their message (e.g. "compare
2hr vs 4hr in South England using the High scenario") — skip re-asking
what they already told you.

## Workflow

### 1. Find out what the client wants to compare — don't guess

Flexplorer has three natural comparison axes: **duration** (1h/2h/4h/8h
etc.), **location** (GB price zone), and **scenario** (Central/High/Low).
Ask which one matters before fetching data — it determines which
investment cases to pull. If they've already said (e.g. "compare 2hr vs
4hr in South England"), skip the question and proceed with that.

### 2. Pick the scenario together

```
flexplorer_list_datasets(regions=["gbr"])
```
to see the accessible `forecast_scenarios`. Identify the most recently
published scenario matching the sensitivity the client is comparing
along (Central by default, or whichever sensitivities are relevant if
they picked scenario as the comparison axis). Never treat "most recent"
as a silent default — surface it as a recommendation and ask:

```
ask_user_input_v0: "Which forecast cycle should I use as the official
basis for this comparison?"
options: ["<latest title> — recommended", "<next most recent title>", "Let me pick a different one"]
```

If the client picked scenario as their comparison axis, this step
instead becomes "which sensitivities" (Central/High/Low) rather than
"which cycle" — confirm the list rather than assuming all three.

### 3. Discover and confirm the investment cases

```
flexplorer_get_scenario(flex_scenario_uuid=...)
```
returns every `investmentCases[]` entry with its config (duration via
`initial_duration_h`, cycles via `daily_cycle_target`, zone via
`location_parameters.bm_zone`, degradation, repowering). Filter this down
to the candidate cases matching the client's chosen zone/year/scenario
along whichever dimension they didn't fix.

Do not pick the final 2-5 cases yourself. Show the candidates (a short
list or table — case title, duration, cycling, vintage) and ask which
ones to load:

```
ask_user_input_v0: "Which durations should I load into the comparison?"
type: multi_select
options: [list of durations found, e.g. "1h", "2h", "4h", "8h"]
```

Cap the suggested options at what's sensible (don't offer 10 durations at
once if the comparison only needs 2-5) but let the client narrow it, not you.
Same goes for vintage/year if more than one is available for the chosen
zone — ask rather than picking the earliest or latest silently.

### 4. Pull each case's revenue data

Go straight to the batched download call — don't spend a round-trip
confirming `currencyOptions` first. `gbp2025` is valid for every GB case;
only fall back to calling `flexplorer_get_investment_case_options` for a
specific case if its download request errors out.

```
flexplorer_get_download_url(requests=[{dataset:"investment_case", flex_scenario_uuid, investment_case_uuid, currency:"gbp2025", basis:"grid"}, ...])
```
in one batched call for all cases. Always use `basis:"grid"` so every case
is normalised per MW of grid connection and directly comparable regardless
of the underlying `bess.ac_rated_export_capacity_mw`.

Fetch and decompress all presigned URLs in one `bash_tool` call, in
parallel, rather than one download per invocation — e.g. loop with `&`
and `wait`, or pass every URL to a single `xargs -P` command. They're
gzip-compressed despite the `.csv` name (`zcat`, don't just `cat`). Then
parse with Python, group by (Year, category) using the mapping in
`references/market_categories.md`, and write one compact JSON file per
case: `{label, region, durationHours, cyclesPerDay, yearly: [{year, energyTrading, frequencyResponse, capacityMarket, networkCharges}]}`.

Keep this preprocessing in Python/bash — do not try to have the artifact
fetch Flexplorer data itself at runtime; artifacts can't call MCP tools.
Embed the finished JSON as a literal object in the artifact code.

### 5. Checkpoint before building the full artifact

The full artifact (five panels, live NPV/IRR, waterfall per case) is the
expensive part to get wrong — don't build it on a guess. Before writing
any artifact code, show the client something cheap first and get a
go-ahead:

- A short inline summary or small chart (e.g. `visualize:show_widget`
  with a simple line/bar comparison of total £/kW/year revenue per loaded
  case) so they can eyeball whether the right cases loaded before you
  invest in the full build.
- Ask directly: does this look right, and should the capex/opex be shared
  across cases or set per-case? (Duration comparisons usually want
  per-case capex since cell cost scales with duration; location/scenario
  comparisons usually don't — but confirm rather than deciding.)

```
ask_user_input_v0: "Capex and opex inputs — same for every case, or one
set per case?"
options: ["Same for all cases", "Separate per case", "Not sure — recommend one"]
```

Only proceed to the full build once the client has confirmed the case
selection looks right and the capex/opex structure. If they want changes
(drop a duration, add a zone), loop back rather than patching the full
artifact afterward.

### 6. Build the artifact

This artifact is delivered as a **standalone downloadable .html file**, not
a `visualize:show_widget` fragment. That distinction matters: a widget
fragment can rely on the host page's CSS variables (`var(--surface-2)`,
`var(--text-primary)`, etc.) and on the visualize tool's "no titles inside
the widget" rule. A standalone file has neither — there is no host page, so
undefined CSS variables silently resolve to nothing (black text on white,
no card backgrounds, no colored legend swatches) and the browser's default
serif font takes over. Concretely, every file this skill produces must be a
complete, self-contained document:

- Start with `<!DOCTYPE html><html lang="en"><head>` — include `<meta charset="UTF-8">`
  and a `<title>`. End with `</body></html>`.
- Define your own `:root { --bg: ...; --card: ...; --border: ...; --text: ...; }`
  block in a `<style>` tag, with a `@media (prefers-color-scheme: dark)`
  override — do not reference `var(--surface-2)` or any other host-only
  token, since nothing defines it outside claude.ai's artifact iframe.
- Explicitly set `body { font-family: -apple-system, BlinkMacSystemFont,
  'Segoe UI', sans-serif; }`. Never leave `font-family` unset — the
  browser default for an unstyled document is serif, which reads as dated
  next to Aurora's own sans-serif report style.
- Every panel gets a visible `<h2>` (or `.case-title`) heading in the page
  itself — "Cashflow stack by market", "NPV waterfall", etc. This is the
  opposite of the visualize-widget rule; a standalone file has no
  surrounding chat message to carry that context, so the titles have to
  live in the document.
- Every legend needs real inline color swatches (a small `<span>` with
  `background: <hex>`) next to the label text, not just a Chart.js legend
  reference that depends on the same undefined host tokens.
- Use the canonical CSS tokens, class names (`.card`, `.legend`, `.tabbtn`,
  `.metric-grid`, `.case-block`, `.badge`), and panel order from the
  "Canonical structure & style" section of `references/chart_types.md` —
  copy that block directly rather than inventing your own. It's the same
  Aurora palette used everywhere else in this skill (amber `#F59E00` for
  energy trading / the highlighted case, dark charcoal `#3C3C3B` for
  frequency response, mid grey `#838383` for capacity market, gold
  `#FFCC00` for network charges) — don't let a generic blue/teal/red
  palette creep back in through Chart.js defaults.
- Only open `references/examples/duration_comparison_reference.html` if you
  need to see the full Chart.js wiring (waterfall bars, pie construction,
  live re-render on input change) worked end to end — `chart_types.md` now
  covers style and structure on its own, so this file is a fallback, not a
  required read.

Read the `frontend-design` skill for the design system, then build a single
HTML or React artifact (see `references/chart_types.md` for the five
panels) with:
- A dropdown/tabs to pick which loaded case's cashflow stack to view
- Number inputs for capex (£/kW), fixed opex (£/kW/yr), discount rate (%),
  asset life (years) — shared or per-case per the client's step-5 answer
- Live NPV/IRR/payback per case using `references/finance_formulas.md`,
  recomputed on every input change
- The ranking panel with the "most cash" badge, sorted live

No prose blocks, no commentary — this mirrors Aurora's charts, not
Aurora's write-up. If the client wants the underlying reasoning, offer to
explain in your chat response, not inside the artifact.

Leave the capex/opex number inputs blank (or clearly marked "enter your
assumption") rather than pre-filled with a guessed placeholder value —
per the guiding principle, don't decide the client's numbers for them
even as a default. If leaving them blank makes the first render of the
chart empty/zeroed, that's fine and expected; say so in chat.

### 7. Sanity-check before presenting

- Confirm the total revenue in your stacked-area chart matches the sum you
  used in the waterfall/NPV panel for the same case — a silent mismatch
  here (e.g. from double-counting a market, or forgetting to exclude
  `Project Total`) is the most likely bug.
- If capex/opex are left at their default (zero, or a placeholder), say so
  out loud in chat — an NPV/IRR built on a zero capex is meaningless and
  the client needs to know to fill it in before trusting the ranking.

## Known limits

- Flexplorer's `investment_case` export is revenue-only — no capex/opex/
  discount rate/NPV/IRR come from the API. Those are always client-typed
  in this skill's artifact (deliberate, per the product decision — do not
  try to source them from Origin's technology-cost tools unless a future
  version of this skill is explicitly extended to do so).
- Co-located (solar+battery) cases follow the same pattern but need extra
  care on the market mapping — see the note in `market_categories.md`.
- This skill is scoped to GB (`region: "gbr"`). Other Flexplorer regions
  may use a different market taxonomy; re-check
  `flexplorer_get_investment_case_options().metadata.markets` before
  reusing the category mapping elsewhere.
