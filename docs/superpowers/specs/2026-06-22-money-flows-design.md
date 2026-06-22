# Money Flows Series — Design Spec

**Date:** 2026-06-22
**Series:** Posts 19–21 (DeltaTheta Build Series)
**Status:** Approved for implementation

---

## Objective

Build a cross-asset capital flow monitor that produces actionable investment positioning intelligence across 2-week to 90-day horizons. Extend the existing sector money flow work (post 13, `tools/sector_money_flow.py`) without modifying it — new tool alongside the existing one.

Primary output: a ranked watchlist with OVERWEIGHT / NEUTRAL / UNDERWEIGHT calls per sector per timeframe, surfacing divergence signals and momentum alignment. Secondary outputs: positioning table (grid view) and heatmap chart.

---

## Scope

**Phase 1 (this spec):** Domestic US sectors + existing asset class proxies
- 11 SPDR sector ETFs (XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY)
- TLT (fixed income proxy)
- GLD (gold proxy)

**Phase 2 (future spec):** Global flows + currencies — international equity ETFs, currency ETFs, DXY. Not in scope here.

---

## Tool

**File:** `tools/capital_flows.py`

Do not modify `tools/sector_money_flow.py`. The new tool reuses the same data fetching pattern (yfinance + curl_cffi, SSL bypass, `.env` load) but is purpose-built around the multi-timeframe signal stack and actionable output model.

### CLI

```
python tools/capital_flows.py              # ranked watchlist (default)
python tools/capital_flows.py --report     # ranked watchlist explicitly
python tools/capital_flows.py --table      # positioning table
python tools/capital_flows.py --chart      # heatmap chart
python tools/capital_flows.py --all        # all three outputs
python tools/capital_flows.py --start 2024-01-01   # override start date
```

CSV is always written to `.tmp/capital_flows_<date>.csv` on every run.

---

## Signal Stack

For each ticker, compute three CMF windows. CMF formula (same as sector tool):

```
MFM = ((Close - Low) - (High - Close)) / (High - Low)
MFV = MFM × Volume
CMF = sum(MFV, window) / sum(Volume, window)   # in [-1, +1]
```

| Window | Label | Horizon |
|--------|-------|---------|
| 5-day  | Short | ~2 weeks |
| 15-day | Medium | ~30 days |
| 30-day | Structural | ~90 days |

### Derived signals (per ticker)

**Momentum alignment score:** Count how many of the three windows agree in sign (all positive = 3/3, two positive one negative = 2/3, etc.). 3/3 agreement = high conviction. 2/3 = moderate. 1/3 or split = watch.

**Positioning call (per timeframe):**
- CMF > +0.05 → OVERWEIGHT
- CMF < −0.05 → UNDERWEIGHT
- Between −0.05 and +0.05 → NEUTRAL

**Divergence flag:** Compare 15-day CMF direction to 15-day price return direction. If CMF is negative but price return is positive → `[DIV↓]` (price rising, flow weakening — distribution signal). If CMF is positive but price return is negative → `[DIV↑]` (price falling, flow holding — accumulation signal).

Divergence thresholds are provisional — adjust after first run if too noisy.

---

## Output Formats

All formats are provisional. Adjust after first run based on what's actually useful.

### Ranked Watchlist (`--report`, default)

Sectors sorted by 15-day CMF (primary sort), strongest inflow to strongest outflow. Each row shows all three window values, alignment score, divergence flag if present, and a positioning call that spans the applicable horizons.

```
Capital Flow Watchlist  —  YYYY-MM-DD
Horizon: 2W / 30D / 90D

  Sector                 5D      15D     30D    Align   Position
  ──────────────────────────────────────────────────────────────────
  Financials           +0.18   +0.14   +0.11   ▲▲▲    OVERWEIGHT  2W–90D
  Technology           +0.12   +0.09   +0.08   ▲▲▲    OVERWEIGHT  2W–90D
  Fixed Income (TLT)   +0.04   +0.15   +0.09   ▲▲▲    OVERWEIGHT  30D–90D
  Materials            +0.06   +0.06   -0.02   ▲▲▼    HOLD / WATCH
  ...
  Consumer Disc        -0.14   -0.20   -0.18   ▼▼▼    UNDERWEIGHT 2W–90D  [DIV↑]
  Gold (GLD)           -0.10   -0.20   -0.15   ▼▼▼    UNDERWEIGHT 2W–90D
```

### Positioning Table (`--table`)

Sector × timeframe grid with OVER / NEUT / UNDER labels. Built for scanning.

```
Sector                  2W        30D       90D
──────────────────────────────────────────────
Financials              OVER      OVER      OVER
Technology              OVER      OVER      OVER
Fixed Income (TLT)      NEUT      OVER      OVER
Materials               OVER      OVER      NEUT
...
Consumer Disc           UNDER     UNDER     UNDER
Gold (GLD)              UNDER     UNDER     UNDER
```

### Heatmap Chart (`--chart`)

Saved to `.tmp/capital_flows_chart_<date>.png`. Rows = sectors, columns = 5/15/30-day windows. Cell color = CMF sign and magnitude: blue = inflow (darker = stronger), red = outflow (darker = stronger), near-zero = light gray. Divergence-flagged tickers get a marker on the cell.

---

## Post Series Arc

### Post 19 — The Flow Lens
Introduce the multi-timeframe tool. Explain the 5/15/30-day signal stack and what each window tells you about positioning horizon. Show the current ranked watchlist and heatmap chart. The actionable read: what to overweight/underweight for the next 2 weeks to 3 months.

CLI output + ranked watchlist table + heatmap chart embedded.

### Post 20 — Reading Rotation
Time-series view: how today's rankings got here. Show flow trends over the past 60–90 days for select sectors — which have been consistently gaining or losing flow, which just flipped. Connect to the classic sector rotation sequence (expansion → peak → contraction → recovery). Current placement on the rotation map.

Requires: time-series output already in the CSV; post adds a multi-line chart of CMF over time for top/bottom sectors.

### Post 21 — When Flow and Price Disagree
Lead with the divergence signal concept. Show current `[DIV]` flagged tickers. Explain what distribution and accumulation divergences historically resolve to. The most actionable setup — price hasn't confirmed what flow is already saying.

Requires: divergence flag already computed; post adds a divergence-specific chart showing price vs CMF overlay for the flagged ticker(s).

---

## File Outputs

| File | Description |
|------|-------------|
| `tools/capital_flows.py` | Main tool |
| `.tmp/capital_flows_<date>.csv` | Wide CMF time series (all windows, all tickers) |
| `.tmp/capital_flows_chart_<date>.png` | Heatmap chart (when `--chart` or `--all`) |

---

## Constraints

- Do not modify `tools/sector_money_flow.py`
- All external data via yfinance only (no new API keys)
- Output formats are provisional — revise after first run
- Paywall structure (free = concept/history, paid = current read) follows posts 17–18 pattern; activate starting post 19 or defer to dashboard series — user decides at publish time
- Posts use actual terminal output from the tool as documentation (per established convention)
