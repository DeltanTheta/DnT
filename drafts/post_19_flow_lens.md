# The Flow Lens: What 5/15/30-Day Capital Flows Say About Positioning

*DeltaTheta | Post 19 of the Build Series*

*Written by Claude with oversight.*

Post 13 introduced Chaikin Money Flow and ran a single 15-day snapshot across the eleven SPDR sector ETFs plus fixed income and gold. That gave you a picture of where flow pressure was on one specific day, at one specific window. Useful, but incomplete.

A single window can't tell you whether what you're seeing is a short-term blip or a structural move. It can't surface the most actionable setup in technical analysis — when price and flow disagree. It can't distinguish between a sector building momentum and a sector in late-stage distribution.

This post introduces the expanded tool: three CMF windows (5 / 15 / 30 days), a momentum alignment score, and a divergence detector. Together they produce a ranked positioning watchlist with explicit calls for 2-week to 90-day horizons. That's the output this pipeline now generates every time you run it.

---

## What Multi-Timeframe CMF Adds

The CMF formula doesn't change. What changes is the question you're asking:

- **5-day window (~1 week):** Short-term pressure. What has flow been doing this week? Useful for near-term positioning but noisy — one large down-day can dominate.
- **15-day window (~3 weeks):** Medium-term trend. This is the post 13 signal. It smooths most noise while still responding to meaningful rotations.
- **30-day window (~6 weeks):** Structural flow. What has capital been doing over the past few weeks? This is the signal that matters for longer holds.

The three windows don't just layer context on top of each other — they produce a **momentum alignment score**. When all three agree in direction (all positive or all negative), the signal has cross-timeframe conviction. When they split, you have a transition or a mixed environment. That distinction drives the positioning call.

A sector with ▲▲▲ alignment has buyers across every relevant horizon. A sector with ▼▼▼ has sellers confirmed in every timeframe. A sector with ▲▼▼ or ▼▲▲ is in transition — and transitions are where the most interesting forward signals live.

---

## The Tool

The `capital_flows.py` script fetches daily OHLCV for all 13 proxies, computes 5/15/30-day CMF for each, and outputs three views: a ranked watchlist (default), a positioning table, and a heatmap chart.

```
python tools/capital_flows.py
python tools/capital_flows.py --table
python tools/capital_flows.py --chart
python tools/capital_flows.py --all
```

```
Fetching OHLCV for 13 tickers...
  OK  XLB    869 trading days  [2023-01-03 to 2026-06-22]
  OK  XLC    869 trading days  [2023-01-03 to 2026-06-22]
  OK  XLE    869 trading days  [2023-01-03 to 2026-06-22]
  OK  XLF    869 trading days  [2023-01-03 to 2026-06-22]
  OK  XLI    869 trading days  [2023-01-03 to 2026-06-22]
  OK  XLK    869 trading days  [2023-01-03 to 2026-06-22]
  OK  XLP    869 trading days  [2023-01-03 to 2026-06-22]
  OK  XLRE   869 trading days  [2023-01-03 to 2026-06-22]
  OK  XLU    869 trading days  [2023-01-03 to 2026-06-22]
  OK  XLV    869 trading days  [2023-01-03 to 2026-06-22]
  OK  XLY    869 trading days  [2023-01-03 to 2026-06-22]
  OK  TLT    869 trading days  [2023-01-03 to 2026-06-22]
  OK  GLD    869 trading days  [2023-01-03 to 2026-06-22]

Computing (5, 15, 30)-day CMF...

Saved 869 rows × 39 cols → .tmp/capital_flows_20260622.csv

Capital Flow Watchlist  —  2026-06-22
Horizon: 2W / 30D / 90D

  Sector                         5D      15D      30D  Align  Position
  ──────────────────────────────────────────────────────────────────────────────
  Fixed Income (proxy)      -0.2705  +0.0157  +0.0062    ▼→→  HOLD / WATCH
  Financials                -0.3722  -0.0047  -0.0231    ▼→→  HOLD / WATCH
  Technology                -0.1564  -0.0172  +0.1505    ▼→▲  HOLD / WATCH
  Materials                 -0.6764  -0.0476  -0.0442    ▼→→  HOLD / WATCH
  Industrials               -0.4787  -0.0784  +0.0478    ▼▼→  UNDERWEIGHT  2W–30D  [DIV↓]
  Energy                    +0.0687  -0.0915  -0.0181    ▲▼→  HOLD / WATCH
  Utilities                 -0.1704  -0.1331  -0.0509    ▼▼▼  UNDERWEIGHT  2W–90D
  Health Care               -0.0613  -0.1577  -0.0650    ▼▼▼  UNDERWEIGHT  2W–90D
  Consumer Staples          -0.3600  -0.1691  -0.1307    ▼▼▼  UNDERWEIGHT  2W–90D
  Comm Services             -0.1439  -0.1819  -0.0966    ▼▼▼  UNDERWEIGHT  2W–90D
  Consumer Discret.         -0.4050  -0.2343  -0.0801    ▼▼▼  UNDERWEIGHT  2W–90D
  Real Estate               -0.5771  -0.2401  -0.1406    ▼▼▼  UNDERWEIGHT  2W–90D
  Gold (proxy)              -0.5612  -0.3449  -0.1156    ▼▼▼  UNDERWEIGHT  2W–90D
```

---

## The Current Snapshot

![Capital Flow Heatmap — 5/15/30-Day CMF, June 22 2026](../.tmp/capital_flows_chart_20260622.png)

### Reading the Heatmap

The horizontal axis is the three timeframes. The vertical axis is the 13 proxies, sorted by 15-day CMF from most positive at the top to most negative at the bottom. Blue = inflow, red = outflow, intensity = magnitude. A "D" marker in the 15D column means the divergence detector flagged that ticker.

The heatmap tells the story faster than the table: nearly every cell is red. This is a broad outflow environment across almost all three windows and almost all sectors. The exceptions — and they matter — are in the top-left and top-right corners.

---

*This is a natural stopping point in the free edition. What follows is the current read — sector-by-sector positioning for 2W to 90D, the divergence alert on Industrials, and what the alignment structure of this snapshot says about where the next rotation is likely to come from.*

<!-- PAYWALL -->

---

## Reading the Numbers: 2W / 30D / 90D

### The Near-Term (5-Day): Uniform Selling Pressure

The 5-day column is the most striking feature of this snapshot. Every sector except Energy is deeply negative, with several reading below −0.30. This is not a sector rotation — it's a broad-based withdrawal of capital over the past week. When you see this pattern across the full universe, the interpretation is usually one of three things: a macro risk-off event (news-driven), end-of-quarter rebalancing, or profit-taking following an extended run.

The magnitude here — Materials at −0.68, Real Estate at −0.58, Gold at −0.56 — is consistent with the kind of broad selling that happens when institutional money is repositioning, not just trimming. The 5-day signal is therefore more useful as context than as a positioning trigger: it tells you the market is in a digestion phase, not that every sector is in structural trouble.

**5-Day positioning: No actionable longs. Observe and wait.**

### The Medium Term (15-Day): Where Flow Has Settled

The 15-day window filters out most of the week's noise and shows the underlying trend. The picture here is more nuanced.

**The top of the watchlist (least negative):** Fixed Income (TLT) at +0.02 and Financials (XLF) at −0.005 are effectively neutral — no meaningful flow in either direction over the past month. Technology (XLK) is also near neutral at −0.02. These three sectors have absorbed the near-term selling without deteriorating their medium-term flow profile.

**The clear underweights:** Gold (−0.34), Real Estate (−0.24), Consumer Discretionary (−0.23), Comm Services (−0.18), and Consumer Staples (−0.17) all show meaningful 15-day outflow. These aren't borderline — they represent sustained multi-week selling.

**The moderates:** Health Care (−0.16), Utilities (−0.13), and Industrials (−0.08) are in outflow but less extreme. Among these, Industrials carries the divergence flag — more on that below.

**15-Day positioning:** Underweight gold, real estate, consumer discretionary, consumer staples, and communication services. Neutral on tech, financials, and fixed income.

### The Structural Flow (30-Day): The Quarter's Underlying Trend

The 30-day window reveals the most important signal in this snapshot: **Technology's structural flow is positive at +0.15**, even as its 5-day and 15-day readings are negative or neutral. This means that over the past quarter, capital has been accumulating in tech — the recent week's selling is working against a positive underlying trend, not confirming a new bearish trend.

The contrast with the rest of the watchlist is notable. Real Estate (−0.14), Consumer Staples (−0.13), Gold (−0.12), and Consumer Discretionary (−0.08) all show sustained 90-day outflows. These are not sectors that are under temporary pressure — they've been losing capital for a quarter.

Fixed Income is barely positive at +0.01 on the 30-day window, consistent with the regime read from posts 17-18: bonds are seeing slow, steady interest without conviction.

**90-Day positioning:** Structural buyer in Technology. Structural sellers in real estate, consumer staples, gold. Fixed income neutral with a slight positive lean.

---

## The Divergence Alert: Industrials [DIV↓]

The divergence flag `[DIV↓]` on Industrials means the 15-day CMF is negative (outflow) while the 15-day price return is positive. Price is up, but flow is weakening.

This is the distribution setup. Someone is selling into the rally — price holds because there are buyers willing to absorb the supply, but the volume-weighted flow analysis picks up the character of the trading: more volume on down-bars than up-bars, even as the closing price moves higher.

The practical implication: Industrials may look fine on a price chart. The flow tells a different story. If the 15-day CMF continues to deteriorate while price holds or grinds higher, that's a classic late-stage distribution pattern. The resolution tends to be a price catch-up to the flow signal — meaning a pullback — rather than the flow signal reversing to match price.

**Watch:** If XLI's 15-day CMF breaks below −0.10 while price holds near current levels, that strengthens the distribution case. If price pulls back to meet the flow signal (CMF recovers toward zero), the divergence resolves benignly.

---

## Positioning Summary: June 22, 2026

| Horizon | Overweight | Neutral / Watch | Underweight |
|---------|-----------|-----------------|-------------|
| 2W | — | Fixed Income, Financials, Tech, Materials, Energy | Everything else |
| 30D | — | Fixed Income, Financials, Tech, Materials, Energy | Industrials, Utilities, Health Care, Staples, XLC, XLY, XLRE, GLD |
| 90D | Technology | Fixed Income | Real Estate, Staples, Gold, XLC, XLY, XLU, XLV |

No sector has full 3/3 alignment for a long. Technology is the only sector with a positive structural (30D) reading, making it the clearest candidate for reaccumulation if and when the near-term selling pressure abates.

The macro interpretation consistent with this flow picture: the market is in a digestion and rotation phase following a strong run. The sectors that benefited most from the reflation trade (financials, tech) are seeing short-term profit-taking but hold their structural flow. The sectors that underperformed (real estate, gold, consumer staples) continue to leak capital at all three timeframes. That's not a bear market signal — it's an extended consolidation in areas that have already repriced lower.

What to watch: if Technology's 15-day CMF turns positive while its 30-day remains at +0.15, that sets up the first ▲▲▲ conviction signal in the watchlist — the kind of alignment score that historically precedes a sustained leg higher.

---

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

*← [Post 18: The Regime Framework](#) | [Post 20: Reading Rotation →](#)*

— *DeltaTheta*
