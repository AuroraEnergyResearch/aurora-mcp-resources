---
name: aus-battery-investment-case
description: Build an interactive Australian NEM battery storage investment-case artifact from Aurora Flexplorer data — revenue-by-market charts, cross-comparison (duration/state/scenario), and a client-editable NPV/IRR/payback waterfall that recommends which option makes the most cash. Use this whenever a client asks to compare battery durations (1hr/2hr/4hr), compare NEM states (NSW/QLD/SA/VIC) or scenarios (Aurora Central/Low/Messy Transition) for storage, or wants "which battery makes the most money" in the NEM. Trigger even if they just say "run the investment case" or name a Flexplorer scenario, state, or duration without asking for a chart explicitly.
---

# AUS (NEM) battery investment case builder

Reproduces Aurora's standard NEM battery investment-case chart types as a
live artifact — charts and numbers only, never Aurora's written
commentary. The client types in their own capex/opex/discount-rate
assumptions and the NPV/IRR ranking recomputes live.

Read `references/chart_types.md` for exact chart specs plus the canonical
CSS/structure to copy, `references/market_categories.md` for the NEM
revenue-category groupings, and `references/finance_formulas.md` for the
JS to embed before writing any code. The full worked HTML example under
`references/examples/` is optional — only open it if you need the Chart.js
wiring in full; the style and panel order are already in `chart_types.md`.

## Guiding principle: ask, don't assume

This skill wraps a multi-step pipeline (multiple MCP calls, a data pull,
an artifact build) around a handful of decisions that are genuinely the
client's to make — which scenario is "official," which durations matter,
whether the ranking should even be built yet. Don't front-load all of
that into one round of questions and then disappear into tool calls for
two minutes. Check in at each decision point, and show something (a
table, a quick chart) before committing to the full build. A client
who's watched their comparison narrow step by step will trust the final
artifact more than one who's handed a finished dashboard cold.

Concretely: never silently pick a scenario, a duration set, or a state on
the client's behalf, even when one option is obviously the newest or most
common choice. Recommend it, explain why in one line, and let them
confirm or override with `ask_user_input_v0`. The only exception is when
the client already gave you the answer in their message (e.g. "compare
2hr vs 4hr in QLD using Aurora Central") — skip re-asking what they
already told you.

## Workflow

### 1. Find out what the client wants to compare — don't guess

The NEM investment cases have three natural comparison axes: **duration**
(1h/2h/4h), **state** (NSW/QLD/SA/VIC), and **scenario** (Aurora Central/
Aurora Low/Messy Transition). Ask which one matters before fetching data —
it determines which investment cases to pull. If they've already said
(e.g. "compare NSW vs SA at 2hr in Aurora Central"), skip the question and
proceed with that.

### 2. Confirm the region code, then pick the scenario together

The Flexplorer region string for the NEM has not been confirmed in this
skill yet — Australia may be `"aus"`, `"nem"`, or something else entirely.
Call

```
flexplorer_list_datasets()
```

without a region filter first, inspect the returned region codes, and use
whichever one corresponds to Australia/NEM from here on. Don't guess
`"aus"` and proceed blind.

Once you have the right region code, call

```
flexplorer_list_datasets(regions=[<confirmed AUS region code>])
```

to see the accessible `forecast_scenarios`. Aurora's own report cycle
names these **Aurora Central**, **Aurora Low**, and **Messy Transition**
— Messy Transition is a distinct upside-volatility case driven by
disorderly coal exits, not a simple high scenario. Identify the most
recently published cycle matching the sensitivity the client is
comparing along. Never treat "most recent" as a silent default —
surface it as a recommendation and ask:

```
ask_user_input_v0: "Which forecast cycle should I use as the official
basis for this comparison?"
options: ["<latest title> — recommended", "<next most recent title>", "Let me pick a different one"]
```

If the client picked scenario as their comparison axis, this step
instead becomes "which scenarios" (Aurora Central/Aurora Low/Messy
Transition) rather than "which cycle" — confirm the list rather than
assuming all three are wanted.

### 3. Discover and confirm the investment cases

```
flexplorer_get_scenario(flex_scenario_uuid=...)
```

returns every `investmentCases[]` entry with its config (duration via
`initial_duration_h`, cycles via `daily_cycle_target`, state/region via
`location_parameters`, degradation, repowering, entry year).
Aurora's own report standardises on **2027-entry and 2030-entry**
(financial year) batteries across the 72 standard cases — confirm which
entry year(s) the client wants alongside state/duration/scenario, since
it's a fourth axis that's easy to forget.

Filter this down to the candidate cases matching the client's chosen
state/entry-year/scenario along whichever dimension they didn't fix.

Do not pick the final 2-5 cases yourself. Show the candidates (a short
list or table — case title, state, duration, cycling, entry year) and ask
which ones to load:

```
ask_user_input_v0: "Which durations should I load into the comparison?"
type: multi_select
options: [list of durations found, e.g. "1h", "2h", "4h"]
```

Cap the suggested options at what's sensible (don't offer every state and
every duration at once if the comparison only needs 2-5 cases) but let
the client narrow it, not you. Same goes for entry year if more than one
is available for the chosen state — ask rather than picking 2027 or 2030
silently.

### 4. Pull each case's revenue data

Unlike the GB skill, don't skip this check — the currency string and the
market-category mapping are both unconfirmed for the NEM (see `Known
limits`). But you only need to run it once per scenario, not once per
case: currency options and the raw `market` list are scenario-level, not
case-level, so pick one representative case from your selection and call

```
flexplorer_get_investment_case_options(flex_scenario_uuid=..., investment_case_uuid=<one representative case>)
```

to confirm the exact currency string (`aud2025` is a placeholder for
"AUD, real 2025" — verify it matches `currencyOptions` rather than
assuming) and to inspect `metadata.markets` against `market_categories.md`'s
mapping before trusting it on a real pull. Reuse both the confirmed
currency string and the verified mapping for every other case in this
comparison — don't repeat the call per case.

Then pull every case in one batched call:

```
flexplorer_get_download_url(requests=[{dataset:"investment_case", flex_scenario_uuid, investment_case_uuid, currency:<confirmed currency string>, basis:"grid"}, ...])
```

Always use `basis:"grid"` so every case is normalised per MW of grid
connection and directly comparable regardless of the underlying nameplate
export capacity.

Fetch and decompress all presigned URLs in one `bash_tool` call, in
parallel, rather than one download per invocation — e.g. loop with `&`
and `wait`, or pass every URL to a single `xargs -P` command. They're
gzip-compressed despite the `.csv` name (`zcat`, don't just `cat`). Then
parse with Python, group by (Year, category) using the confirmed mapping,
and write one compact JSON file per case: `{label, state, durationHours, cyclesPerDay, entryYear, yearly: [{year, energyRevenue, regulationFcas, contingencyFcas}]}`.

Keep this preprocessing in Python/bash — do not try to have the artifact
fetch Flexplorer data itself at runtime; artifacts can't call MCP tools.
Embed the finished JSON as a literal object in the artifact code.

### 5. Checkpoint before building the full artifact

The full artifact (five panels, live NPV/IRR, waterfall per case) is the
expensive part to get wrong — don't build it on a guess. Before writing
any artifact code, show the client something cheap first and get a
go-ahead:

- A short inline summary or small chart (e.g. `visualize:show_widget`
  with a simple line/bar comparison of total A$/kW/year revenue per
  loaded case) so they can eyeball whether the right cases loaded before
  you invest in the full build.
- Ask directly: does this look right, and should the capex/opex be shared
  across cases or set per-case? (Duration comparisons usually want
  per-case capex since cell cost scales with duration; state/scenario
  comparisons usually don't — but confirm rather than deciding.)

```
ask_user_input_v0: "Capex and opex inputs — same for every case, or one
set per case?"
options: ["Same for all cases", "Separate per case", "Not sure — recommend one"]
```

Only proceed to the full build once the client has confirmed the case
selection looks right and the capex/opex structure. If they want changes
(drop a duration, add a state), loop back rather than patching the full
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
  energy revenue / the highlighted case, dark charcoal `#3C3C3B` for
  regulation FCAS, mid grey `#838383` for contingency FCAS) — don't let a
  generic blue/teal/red palette creep back in through Chart.js defaults.
  Only three revenue categories exist for the NEM — don't add a fourth
  "network charges" bucket or borrow the GB skill's fourth colour.
- Only open `references/examples/duration_comparison_reference.html` if you
  need to see the full Chart.js wiring (waterfall bars, pie construction,
  live re-render on input change) worked end to end — `chart_types.md` now
  covers style and structure on its own, so this file is a fallback, not a
  required read.

Read the `frontend-design` skill for the design system, then build a
single HTML or React artifact (see `references/chart_types.md` for the
five panels) with:
- A dropdown/tabs to pick which loaded case's cashflow stack to view
- Number inputs for capex (A$/kW), fixed opex (A$/kW/yr), discount rate
  (%, Aurora's own convention is 11% real — see `finance_formulas.md`),
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
  here (e.g. from double-counting a market, or forgetting to exclude a
  redundant total row) is the most likely bug.
- Cross-check at least one loaded case against Aurora's own published
  numbers if it's a standard 2027- or 2030-entry, 1h/2h/4h case in
  NSW/QLD/SA/VIC — the Present Value of Revenue and IRR table in the
  report (Standard battery investment cases section) gives exact
  benchmark figures at an 11% real discount rate. A large unexplained gap
  usually means a market was mis-bucketed, not that the client's inputs
  are wrong.
- If capex/opex are left at their default (zero, or a placeholder), say so
  out loud in chat — an NPV/IRR built on a zero capex is meaningless and
  the client needs to know to fill it in before trusting the ranking.

## AUS conventions at a glance

- **Comparison axes**: state (NSW/QLD/SA/VIC), duration (1h/2h/4h), or
  scenario (Aurora Central/Aurora Low/Messy Transition).
- **Revenue categories**: three buckets — Energy revenue, Regulation
  FCAS, Contingency FCAS. See `market_categories.md` for the important
  nuance that "Energy revenue" already nets in FCAS utilisation
  (spot-price) payments, distinct from the FCAS *capacity* payments in
  the other two buckets.
- **Durations**: standard cases are 1h/2h/4h.
- **Entry years**: Aurora's own report anchors comparisons on 2027-entry
  and 2030-entry batteries (financial year) — two entry years, not one.
- **Region code**: unconfirmed — verify via `flexplorer_list_datasets()`
  before assuming `"aus"` (see step 2).

## Known limits

- Flexplorer's `investment_case` export is revenue-only — no capex/opex/
  discount rate/NPV/IRR come from the API. Those are always client-typed
  in this skill's artifact (deliberate, per the product decision — do not
  try to source them from Origin's technology-cost tools unless a future
  version of this skill is explicitly extended to do so).
- The market-category mapping in `market_categories.md` was inferred from
  Aurora's published chart legends (Energy revenue / Regulation FCAS /
  Contingency FCAS), not from a live inspection of the raw Flexplorer
  `market` strings for the NEM — always verify against
  `flexplorer_get_investment_case_options().metadata.markets` before
  trusting it on a real pull, and update the reference file once
  confirmed.
- Co-located (solar+battery) cases are not covered by this skill yet —
  the AUS report's standard investment cases are battery-only. If a
  client asks for a co-located NEM case, treat it as an extension and
  check the Flexplorer export format from scratch rather than assuming
  a standalone-case pattern applies unchanged.
