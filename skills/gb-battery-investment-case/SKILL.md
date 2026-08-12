---
name: gb-battery-investment-case
description: Builds an interactive GB battery investment-case artifact from Aurora Flexplorer data — revenue-by-market charts plus a client-editable NPV/IRR/payback ranking. Use whenever a client compares battery durations, GB price zones, or forecast scenarios for storage, or asks which battery makes the most money — including bare asks like "run the investment case" or a named Flexplorer scenario, zone or duration with no chart mentioned.
---

# GB battery investment case builder

Reproduces Aurora's standard battery investment-case charts as one live
artifact — charts and numbers only, never Aurora's written commentary. The
client types their own capex/opex/discount-rate assumptions and the NPV/IRR
ranking recomputes live.

Read before writing any code: `references/chart_types.md` (the five panels,
canonical CSS and structure, Aurora palette), `references/market_categories.md`
(Flexplorer market groupings), `references/finance_formulas.md` (the JS to
embed).

## Checkpoints

Four decisions in this pipeline belong to the client: the comparison axis, the
forecast scenario, the case list, and the capex/opex structure. Each is a
**checkpoint** — recommend one option with a one-line reason, then wait for an
`ask_user_input_v0` answer before spending the next round of tool calls. A
checkpoint the client's opening message already answers ("compare 2hr vs 4hr in
South England using the High scenario") is answered; carry on.

The pipeline is slow — several MCP calls, a data pull, an artifact build — so
each checkpoint also gives the client something to look at while the comparison
narrows, instead of two silent minutes and a finished dashboard.

## Workflow

### 1. Checkpoint: comparison axis

Flexplorer compares along three axes: **duration** (1h/2h/4h/8h), **location**
(GB price zone), and **scenario** (Central/High/Low). The answer decides which
investment cases to pull, so settle it before fetching anything.

### 2. Checkpoint: forecast scenario

```
flexplorer_list_datasets(regions=["gbr"])
```
lists the accessible `forecast_scenarios`. Recommend the most recently
published cycle matching the client's sensitivity (Central unless they said
otherwise) and confirm it:

```
ask_user_input_v0: "Which forecast cycle should I use as the official
basis for this comparison?"
options: ["<latest title> — recommended", "<next most recent title>", "Let me pick a different one"]
```

When scenario is the comparison axis, this checkpoint becomes "which
sensitivities" (Central/High/Low) rather than "which cycle" — confirm the list.

### 3. Checkpoint: which investment cases

```
flexplorer_get_scenario(flex_scenario_uuid=...)
```
returns every `investmentCases[]` entry with its config: duration
(`initial_duration_h`), cycling (`daily_cycle_target`), zone
(`location_parameters.bm_zone`), degradation, repowering. Filter to the
candidates matching the client's fixed dimensions, show them as a short table
(title, duration, cycling, vintage), and let the client pick the 2-5 to load:

```
ask_user_input_v0: "Which durations should I load into the comparison?"
type: multi_select
options: [durations found, e.g. "1h", "2h", "4h", "8h"]
```

Offer the handful that fit the comparison rather than every case found. Where
more than one vintage or year exists for the chosen zone, that is a checkpoint
too.

### 4. Pull each case's revenue data

Go straight to the batched download — `gbp2025` is valid for every GB case;
call `flexplorer_get_investment_case_options` only if a download request errors
out.

```
flexplorer_get_download_url(requests=[{dataset:"investment_case", flex_scenario_uuid, investment_case_uuid, currency:"gbp2025", basis:"grid"}, ...])
```

`basis:"grid"` normalises every case per MW of grid connection, so cases stay
comparable regardless of `bess.ac_rated_export_capacity_mw`.

Fetch and decompress all presigned URLs in a single parallel `bash_tool` call
(`&` plus `wait`, or one `xargs -P`). They are gzip-compressed despite the
`.csv` name — `zcat`. Then parse with Python, group by (Year, category) using
`references/market_categories.md`, and write one compact JSON file per case:
`{label, region, durationHours, cyclesPerDay, yearly: [{year, energyTrading, frequencyResponse, capacityMarket, networkCharges}]}`.

Artifacts can't call MCP tools, so all preprocessing stays in Python/bash and
the finished JSON is embedded in the artifact as a literal object.

### 5. Checkpoint: preview and capex/opex structure

The five-panel artifact is the expensive thing to get wrong, so show something
cheap first: a `visualize:show_widget` comparison of total £/kW/year per loaded
case, so the client can confirm the right cases loaded. Then:

```
ask_user_input_v0: "Capex and opex inputs — same for every case, or one
set per case?"
options: ["Same for all cases", "Separate per case", "Not sure — recommend one"]
```

Duration comparisons usually want per-case capex, since cell cost scales with
duration; location and scenario comparisons usually don't — recommend on that
basis. If the client wants a different case set, loop back to step 3 rather
than patching the finished artifact.

### 6. Build the artifact

Deliver a **standalone downloadable .html file**, not a `visualize:show_widget`
fragment. With no host page, the file supplies its own CSS variables, fonts and
panel headings: copy the `:root` token block, class names, palette and panel
order from "Canonical structure & style" in `references/chart_types.md`
verbatim, and follow the standalone-file rules alongside it.

Read the `frontend-design` skill for the design system, then build the five
panels with:
- Tabs to pick which loaded case's cashflow stack to view
- Number inputs for capex (£/kW), fixed opex (£/kW/yr), discount rate (%),
  asset life (years) — shared or per-case per the step-5 answer
- Live NPV/IRR/payback per case using `references/finance_formulas.md`,
  recomputed on every input change
- The ranking panel with the "most cash" badge, sorted live

Labels, numbers and legends only — this mirrors Aurora's charts, not Aurora's
write-up. Offer the underlying reasoning in your chat response instead.

Leave the capex/opex inputs blank and marked "enter your assumption" — the
client's numbers are theirs to set (checkpoint), so a zeroed first render is
expected. Say so in chat.

### 7. Verify before presenting

Done when both hold:
- For every loaded case, the stacked-area total equals the revenue sum feeding
  that case's waterfall/NPV panel. Mismatches come from double-counting a
  market or including `Project Total`.
- Any capex or opex still blank or zero is called out in chat — an NPV/IRR
  built on zero capex is meaningless and the client needs to fill it in before
  trusting the ranking.

## Known limits

- Flexplorer's `investment_case` export is revenue-only: capex, opex, discount
  rate, NPV and IRR are always client-typed here. Product decision — sourcing
  them from Origin's technology-cost tools needs an explicit extension to this
  skill.
- Co-located (solar+battery) cases follow the same pattern with extra care on
  the market mapping — see the note in `market_categories.md`.
- Scoped to GB (`region: "gbr"`). Other Flexplorer regions may use a different
  market taxonomy; re-check
  `flexplorer_get_investment_case_options().metadata.markets` before reusing the
  category mapping elsewhere.
