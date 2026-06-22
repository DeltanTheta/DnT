# Post 16 — The Spread Spectrum: Design Spec

**Date:** 2026-06-21
**Post:** #16 of the DeltaTheta Build Series (Credit Spreads arc, post 3 of 5)
**Status:** Approved

---

## Objective

Show that credit is not monolithic. Three tiers — IG, HY, CCC — price three different layers of risk and move on different timelines during stress events. The gap between them (the quality premium) is its own signal. Post extends `tools/credit_spreads.py` to surface this automatically.

---

## Tool Extension: `tools/credit_spreads.py`

Two additions, no new CLI flags:

### 1. `print_summary()` — differential row
When both `"HY"` and `"IG"` are present in the fetched dataframe, compute `HY - IG` and append a separator + row to the existing table:

```
--------------------------------------------------------------------
  HY–IG Quality Premium        1.89%     ...      ...      ...%    ...
====================================================================
```

Same columns as other rows (current, 52W low/high, percentile rank, WoW change). Label: `"HY–IG Quality Premium"`. Percentile rank computed over the history where both HY and IG are available (use the intersection of the two series' date ranges).

### 2. `make_chart()` — two-panel layout
When `"HY"` and `"IG"` are both present, split the figure into two vertically stacked panels (height ratio 3:1):
- **Top panel:** existing spread lines (HY, IG, CCC if requested), recession shading, current-value annotations
- **Bottom panel:** HY–IG differential line in a neutral color (e.g. `#aaaaaa`), horizontal reference line at the full-period median differential, no recession shading (would duplicate the top panel), minimal axis labels

When only one series is requested (no differential computable), fall back to the existing single-panel layout.

Chart output filename: `credit_spreads_YYYYMMDD.png` (unchanged).

### 3. `make_stack_chart()` — tier stack chart (new)

A second chart output showing the credit spectrum as stacked filled areas. Generated automatically alongside the existing chart whenever `--chart` is used and HY + IG are both present.

**Layout:** Single panel, same dark background and date range as the main chart.

**Layers (bottom to top):**

- **IG base:** filled area from 0 to `IG OAS`, color `#4a9eff`, alpha 0.5 — the floor of corporate credit risk premium
- **HY–IG quality premium band:** filled area from `IG OAS` to `HY OAS`, color `#f5a623`, alpha 0.5 — shows how much extra you pay to go leveraged
- **CCC–HY band (if CCC fetched):** filled area from `HY OAS` to `CCC OAS`, color `#e05c5c`, alpha 0.5 — the distressed tier premium

Draw a thin boundary line at the top of each filled band (same color as fill, full opacity, lw 1.2) so the tiers are legible.

Add recession shading (same `#c0392b`, alpha 0.12) so stress periods are visible against the fill.

**Annotations:** Label each band on the right edge with its current OAS value and name (e.g. "IG 0.74%", "Quality Premium 1.89%", "CCC premium X%"). Use the fill color for each label.

**Title:** `"Credit Spread Stack — [date]"`

Chart output filename: `credit_spreads_stack_YYYYMMDD.png`.

---

## Post Structure

### 1. Opening hook
Lead with the core insight: the spread number you saw in post 15 is an aggregate. Underneath it are three quality tiers pricing three completely different risks. The tier you look at — and the gap between them — changes what the signal means.

No definitions yet. Hook first.

### 2. The three tiers

**Investment Grade (IG) — BBB and above**
- Large, established issuers with access to capital markets
- Spread primarily reflects liquidity risk and macro rate environment, not idiosyncratic default probability
- Typical range in non-recessionary periods: 50–150bps
- Widens when the whole system is under stress (2008, 2020); relatively stable otherwise

**High Yield (HY) — BB and below**
- Leveraged issuers with thinner coverage ratios
- Spread reflects both idiosyncratic default risk and macro conditions
- Much more volatile than IG; leads IG into stress, leads IG out of it too
- Typical non-recessionary range: 250–500bps; peaks >1000bps in severe stress (2008: ~2000bps, 2020: ~1100bps)

**CCC — the distressed tier**
- Companies that are already under significant financial pressure
- When CCC spreads exceed ~1000bps, the market is pricing near-certain restructuring for a meaningful fraction of the index
- Not a leading indicator — it's a concurrent or lagging one; by the time CCC blows out, the stress event is already underway
- Useful as a severity gauge, not an early warning

Include a simple tier table showing: tier, typical range (calm), typical range (stress), what primarily drives it.

### 3. The quality premium (HY–IG differential)

The differential between HY and IG OAS is a distinct signal:
- **Compressed differential:** market isn't differentiating much by quality — cheap capital flows across the quality stack. Historically precedes either sustained expansion or a sharp reversal when the tide turns.
- **Widening differential:** re-pricing is underway specifically for weaker borrowers. Systemic risk hasn't necessarily arrived, but credit discrimination has.
- Historical context: what the median differential looks like and how it behaves going into stress periods.

### 4. The tool

CLI commands to include with actual terminal output:

```
python tools/credit_spreads.py --series HY IG CCC --chart
```

Show full output: fetch lines, the snapshot table including the HY–IG differential row, and the chart save line. Run this fresh the day the post is written to get a live reading.

### 5. Today's reading (live)

Table: all three tiers + HY–IG differential row, with percentile ranks.

Two charts embedded in sequence:

1. `![Credit Spread History — HY, IG, CCC](../.tmp/credit_spreads_YYYYMMDD.png)` — two-panel time-series + differential below
2. `![Credit Spread Stack — Tier Hierarchy](../.tmp/credit_spreads_stack_YYYYMMDD.png)` — tier stack showing IG base / quality premium / CCC band

From post 15: HY at 2.63% (1.4th pct), IG at 0.74% (1.0th pct). CCC reading and all percentile ranks to be fetched fresh the day the draft is written.

### 6. Interpretation

Three simultaneous observations:
1. **All three tiers at or near historical lows** — not just HY and IG; CCC is also compressed. This is broad-based, not tier-specific.
2. **Quality premium compressed** — the market is not differentiating. Weak and strong borrowers are being priced nearly the same relative to history.
3. **Directionality:** week-over-week still tightening (from post 15: HY -17bps in prior week). The move is still in the same direction.

Two reads (consistent with post 15 framing):
- **Benign:** Capital is abundant, refinancing conditions favorable, default risk genuinely low. The market is pricing reality correctly.
- **Skeptical:** When quality premia collapse, it means investors have stopped asking hard questions about credit quality. That's the condition that precedes repricing — not the repricing itself. The setup is asymmetric: limited upside in spreads from here, meaningful downside if anything disturbs the consensus.

No position taken. The pipeline reads; the reader decides.

### 7. Tease post 17

"The next post turns this into a cross-asset signal. We'll look at the historical relationship between credit spreads and equity — whether spread moves lead or lag equity turns and what the current configuration implies."

### 8. BMC button

```
[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)
```

---

## Series Navigation

Bottom of post (after BMC, before signature):
```
← Post 15: OAS 101 | Post 17: Credit vs Equity →
```

---

## Images Required

Both charts generated by a single `python tools/credit_spreads.py --series HY IG CCC --chart` run:

- `credit_spreads_YYYYMMDD.png` — two-panel time-series + differential (existing chart, extended)
- `credit_spreads_stack_YYYYMMDD.png` — new tier stack chart

Both embedded in the "Today's Reading" section of the post. Time-series first (historical context), tier stack second (current hierarchy at a glance).

---

## Constraints

- Run `credit_spreads.py` fresh the day the draft is written to capture live data
- CCC series (`BAMLH0A3HYC`) already in `SERIES_MAP` — no new FRED IDs needed
- Do not add new CLI flags; the differential appears automatically when HY and IG are both fetched
- Follow post 15 tone: precise but not academic, no hedging on the mechanics, two reads on the interpretation
