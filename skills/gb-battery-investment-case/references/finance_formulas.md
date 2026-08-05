# NPV / IRR / payback formulas (client-side JS)

Flexplorer gives modelled annual revenue only. Capex, fixed opex, discount
rate, and asset life are typed in by the client in the artifact — compute
everything else client-side so it updates live as they edit inputs.

## Cashflow construction (per investment case)

```
year 0:        -capex
years 1..N:    revenue[year] - fixedOpex   (N = asset life, or truncate/pad
                                             the Flexplorer series to N years)
optional:      -repoweringCapex in the client-specified repowering year
optional:      +salvageValue in the final year
```

Revenue for each year is the sum of the four category buckets from
`market_categories.md`. Use real terms throughout (Flexplorer's `gbp2025` or
similar currency option) — do not mix nominal and real cashflows.

## NPV

```js
function npv(rate, cashflows) {
  return cashflows.reduce((acc, cf, t) => acc + cf / Math.pow(1 + rate, t), 0);
}
```

## IRR (Newton-Raphson, falls back to bisection)

```js
function irr(cashflows, guess = 0.1) {
  let rate = guess;
  for (let i = 0; i < 100; i++) {
    const npvVal = npv(rate, cashflows);
    const d = 1e-6;
    const deriv = (npv(rate + d, cashflows) - npvVal) / d;
    if (Math.abs(deriv) < 1e-9) break;
    const next = rate - npvVal / deriv;
    if (Math.abs(next - rate) < 1e-7) return next;
    rate = next;
  }
  // bisection fallback if Newton didn't converge or diverged outside sane bounds
  if (!isFinite(rate) || rate < -0.99 || rate > 5) {
    let lo = -0.5, hi = 2;
    for (let i = 0; i < 200; i++) {
      const mid = (lo + hi) / 2;
      if (npv(lo, cashflows) * npv(mid, cashflows) <= 0) hi = mid; else lo = mid;
    }
    return (lo + hi) / 2;
  }
  return rate;
}
```

Return `null`/`NaN` gracefully if cashflows never cross zero (e.g. capex
entered as 0) — display "n/a" in the UI rather than a garbage number.

## Payback period (simple, undiscounted — matches Aurora's own convention)

```js
function paybackYears(cashflows) {
  let cumulative = cashflows[0]; // capex, negative
  for (let t = 1; t < cashflows.length; t++) {
    cumulative += cashflows[t];
    if (cumulative >= 0) {
      // linear interpolation within the year for a fractional payback
      const prev = cumulative - cashflows[t];
      const frac = -prev / cashflows[t];
      return t - 1 + frac;
    }
  }
  return null; // never pays back within asset life
}
```

## Recommendation logic

Rank all loaded cases by NPV (primary) at the client's current assumptions.
Recompute the ranking live on every input change — the "most cash" badge
must never be a static, one-time judgement baked in from a single run.
Break ties (within 1% of top NPV) by showing both as joint-best rather than
arbitrarily picking one.
