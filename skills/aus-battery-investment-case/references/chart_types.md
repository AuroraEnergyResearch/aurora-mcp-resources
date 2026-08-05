# Chart types to reproduce (charts only, no commentary bullets)

Build these as panels in one interactive artifact. Never include Aurora's
written commentary text (the bulleted "why" paragraphs beside each chart in
the source report, e.g. "Battery gross margins are expected to improve
late-2030s as coal closes...") — clients get the chart, the numbers, and
the recommendation badge only.

## 1. Cashflow stack over time
Stacked bar/area chart, A$/kW/year, x-axis = year, one series per category
from `market_categories.md` (Energy revenue, Regulation FCAS, Contingency
FCAS). One chart per selected investment case, or a dropdown to switch
between loaded cases. Aurora's own version overlays a black line for total
gross margin on top of the stack — reproduce that if it doesn't clutter
the chart, otherwise the stack total is sufficient.

## 2. Cross-comparison line chart
Same y-axis (A$/kW total gross margin/revenue, i.e. sum of all categories),
one line per option along whichever dimension the client picked (state,
duration, or scenario). This is the chart that needs the client's answer
to "what do you want to compare" — ask before fetching data, since it
decides which Flexplorer investment cases to pull (see SKILL.md workflow).
Aurora's own report also shows a "between quarters" delta version (current
cycle vs prior cycle, with a PV-of-revenue-impact badge) — only build that
if the client explicitly wants a quarter-on-quarter comparison rather than
a state/duration/scenario comparison.

## 3. Energy vs FCAS revenue split pies
One small pie per case: Energy revenue % vs (Regulation FCAS + Contingency
FCAS) %, computed as share of total lifetime revenue (not time-based,
revenue-based — simpler and the number that actually matters for cash).
Label each pie with its case (e.g. "2h, NSW, 2027-entry"). Aurora's own
commentary notes FCAS is consistently the smaller share in the NEM
(wholesale arbitrage dominates) — the pies should make that visible without
restating it as text.

## 4. NPV waterfall + IRR + payback
Per case: waterfall bars for -Capex, -Fixed Opex (lifetime sum, negative),
+Energy revenue, +Regulation FCAS, +Contingency FCAS (sum to net), +Salvage
value (if set) -> NPV bar. Below the waterfall show three stat tiles:
Unlevered IRR, Payback period, NPV per kW. Render one waterfall per loaded
case side by side (2-4 max before it gets cramped — use a horizontal
scroll or tabs beyond that).

Aurora's own report presents this same underlying data as a flat summary
table (Entry Year x State x Scenario x Duration -> PV of Revenue and IRR) —
useful as a sanity-check reference (see SKILL.md step 7) but the artifact
itself should render waterfalls, not reproduce that table verbatim.

## 5. Ranking / recommendation
A simple sorted bar chart of NPV or IRR across all loaded cases, with the
top case visually highlighted (accent border, per frontend-design system)
and a one-line badge: "Highest NPV: 4-hour, SA (2027-entry) — A$X.XXm/MW".
Recompute and re-sort live whenever capex/opex/discount rate inputs change.

**The NPV/IRR toggle is a required control, not optional phrasing.** Render
it as an actual segmented pill toggle (two buttons, active state filled
with `var(--bg-accent)`/`var(--text-accent)`, inactive state transparent
with `var(--border)`) sitting directly above the ranking chart — not a
sentence describing that toggling is possible. Switching it must re-sort
the bars and update the badge text (NPV badge reads "…—  A$X.XXm/MW", IRR
badge reads "…— X.X% IRR") without a page reload. This is the single most
noticeable difference between a client-approved build and a rejected one —
do not skip it or leave it as a TODO.

## Visual style — sleek, not report-like
Aurora's own PDF report is dense and serif-adjacent; the artifact should
read as the opposite of that. Concretely:
- No section headers that mimic report chapter titles (no "Figure 3:",
  no numbered chart captions). Controls and charts should sit close
  together with minimal label text — a compact toggle or dropdown is the
  label.
- Default to Anthropic Sans everywhere. Only use `var(--font-voice)`
  (serif) for a single hero NPV/IRR figure if you want one stat to read
  as the headline number — never for headers, labels, or body text, and
  never for more than one figure on the page.
- Metric tiles (NPV/IRR/payback) stay compact: `var(--surface-1)` card,
  no border, 12px label + 24px/500 value — not larger, not boxed in a
  bordered card on top of the tile background.
- Keep vertical rhythm tight: prefer stacked controls with 8-12px gaps
  over full-width section dividers or heavy whitespace between panels.
- Every toggle, dropdown, and select should look like it belongs in the
  same compact control row — same height, same border treatment — rather
  than mixing bare `<select>` chrome with custom-styled buttons.

## Aurora chart palette
Use Aurora's own brand colours (from the AURORA Refresh theme), not the
generic Cove categorical palette — this keeps every chart in-brand without
pulling in any logo or template artwork.

| Role | Hex | Use for |
|------|-----|---------|
| Amber (accent 1) | `#F59E00` | Energy revenue; the highlighted/top case in the ranking chart |
| Dark charcoal (text/dk1) | `#3C3C3B` | Regulation FCAS; axis labels, chart text |
| Mid grey (accent 5) | `#838383` | Contingency FCAS; non-highlighted ranking bars |
| Gold (accent 2) | `#FFCC00` | Fourth series in a cross-comparison chart (e.g. a fourth state or duration) |
| Light gold (accent 3) | `#FFE680` | Fifth series if the comparison needs one |
| Light grey (accent 6) | `#B1B1B0` | Sixth series, or gridlines/recessive chrome |

Concretely:
- **Cashflow stack** (chart 1): Energy revenue = amber `#F59E00`,
  Regulation FCAS = dark charcoal `#3C3C3B`, Contingency FCAS = mid grey
  `#838383`.
- **Cross-comparison** (chart 2): assign amber, dark charcoal, mid grey,
  then gold in that order as each additional state/duration/scenario is
  added — this matches the order Aurora's own theme cycles chart series
  in PowerPoint.
- **Ranking** (chart 5): the top case is amber `#F59E00`; every other bar
  is light grey `#B1B1B0`, per the "one hue + gray" emphasis pattern.
- Keep the light surfaces from the theme (`#FFFFFF`, `#E7E7E7`) as chart
  backgrounds/gridlines rather than introducing new neutrals.

## Canonical structure & style (copy this, don't invent your own)

Every standalone artifact this skill produces follows this exact skeleton
and CSS token set — same `:root` variables, same class names, same panel
order top to bottom. This is what replaces reading the full worked-example
HTML file; only open
`references/examples/duration_comparison_reference.html` if you need to
see the Chart.js wiring or finance-JS integration in full (rare — the
formulas already live in `finance_formulas.md`).

**CSS tokens** (light, with a `@media (prefers-color-scheme: dark)` override):
```css
:root{
  --bg:#fcfcfb; --card:#ffffff; --border:#e1e0d9; --border-strong:#c3c2b7;
  --text:#0b0b0b; --text-2:#52514e; --text-mut:#898781;
  --amber:#F59E00; --charcoal:#3C3C3B; --accent-bg:#fdf1dc;
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#141413; --card:#1a1a19; --border:#2c2c2a; --border-strong:#383835;
    --text:#ffffff; --text-2:#c3c2b7; --text-mut:#898781;
    --amber:#F59E00; --charcoal:#c3c2b7; --accent-bg:#3a2c0f;
  }
}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);padding:1.5rem;}
.card{background:var(--card);border:0.5px solid var(--border);border-radius:12px;padding:1rem 1.25rem;margin-bottom:1.25rem;}
.row{display:flex;gap:1.25rem;flex-wrap:wrap;}
.legend{display:flex;flex-wrap:wrap;gap:16px;margin-bottom:8px;font-size:12px;color:var(--text-2);}
.legend span.sw{width:10px;height:10px;border-radius:2px;display:inline-block;margin-right:4px;}
.tabbtn{font-size:13px;padding:6px 14px;border:0.5px solid var(--border-strong);background:transparent;color:var(--text);border-radius:8px;cursor:pointer;}
.tabbtn.active{background:var(--accent-bg);border-color:var(--amber);color:var(--amber);}
.metric-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:12px;}
.metric .lab{font-size:12px;color:var(--text-mut);margin:0 0 4px;}
.metric .val{font-size:20px;font-weight:500;margin:0;}
.inputs{display:grid;grid-template-columns:repeat(2,1fr);gap:10px 16px;margin-bottom:10px;}
.inputs input{width:100%;height:32px;font-size:13px;border:0.5px solid var(--border-strong);border-radius:6px;padding:0 8px;background:var(--card);color:var(--text);}
.case-block{border:0.5px solid var(--border);border-radius:10px;padding:0.75rem 1rem;margin-bottom:0.75rem;}
.case-title{font-size:14px;font-weight:500;margin:0 0 8px;}
.badge{display:inline-block;background:var(--accent-bg);color:var(--amber);font-size:12px;padding:4px 12px;border-radius:8px;margin-bottom:10px;}
```

**Panel order** (top to bottom, always — don't reorder or interleave):
1. `<h1>` title + `.sub` one-line assumptions summary (state, scenario,
   entry year, figures in real A$2025, per kW of grid connection)
2. `.card` — Cashflow stack by market (chart 1), with a `.toggle-row` of
   `.tabbtn` to switch case if more than one is loaded. Only three stack
   series: Energy revenue, Regulation FCAS, Contingency FCAS
3. `.card` — Cross-comparison line chart (chart 2), with a `.legend`
   above the canvas
4. `.card` — Revenue-mix pies (chart 3), one `.pie-block` per case inside
   a flex row (Energy revenue % vs FCAS %)
5. `.card` — Assumptions: shared discount-rate/asset-life `.inputs` row
   (discount rate placeholder should reference Aurora's 11% real
   convention), then one `.case-block` per case with its own capex/opex
   `.inputs` in A$/kW
6. `.row` of `.card`s — NPV waterfall + `.metric-grid` (IRR/payback/NPV
   tiles) per case, side by side
7. `.card` — Ranking, with the NPV/IRR `.tabbtn` toggle and `.badge`
   recommendation text above the bar chart

Every input in step 5 wires to a single `computeAndRender()`-style function
that recomputes NPV/IRR/payback/waterfall/ranking together, so nothing
should be left stale after one field changes.

## Non-negotiables
- No prose paragraphs inside the artifact — labels, numbers, legends only.
- One y-axis per chart (per house style) — never dual-axis.
- Use the Aurora chart palette above for every chart in this artifact —
  no Cove palette, no rainbow.
- Only three revenue categories exist for the NEM (see
  `market_categories.md`): Energy revenue, Regulation FCAS, Contingency
  FCAS. Don't invent a fourth category or a Capacity Market / Network
  Charges legend for an AUS chart.
