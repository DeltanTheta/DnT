# The Hidden Buyers and Sellers: Volatility Control Funds and the Realized Vol Term Structure

*DeltaTheta | Post 11 of the Build Series*

*Written by Claude with oversight.*

Most market participants spend their time trying to figure out what earnings will be, where rates are headed, or what the Fed will do next. But there is a large class of institutional player that does none of that. They don't have a macro view. They don't analyze fundamentals. They buy and sell based on a single number — realized volatility — and the mechanics of what they do when that number changes is a structural market force worth understanding.

This post introduces those players, explains why the *term structure* of realized volatility is the right tool for tracking their behavior, and shows how to measure it with freely available data.

*For background on realized volatility, implied volatility, and the Volatility Risk Premium, see [Post 10 — Volatility: What the Options Market Is Pricing as Risk](https://deltantheta.substack.com/p/volatility-what-the-options-market).*

---

## Who Are These Funds?

Volatility-targeting — also called vol control — is a systematic approach to portfolio management where position size is continuously adjusted to maintain a target level of volatility. The core equation is straightforward:

```text
Position Size = Target Volatility / Realized Volatility
```

If the target is 10% annualized vol and the market has been running at 10%, you hold a full position. If realized vol spikes to 20%, you cut exposure in half. If it drops to 5%, you lever up to 2x. The goal is a portfolio that experiences consistent volatility over time — not one with a fixed notional allocation.

This isn't a niche strategy. It shows up in several significant pockets of institutional capital:

- **Risk parity funds** allocate to each asset class based on its risk contribution rather than dollar weight. When vol rises in one sleeve, they sell it.
- **Target-volatility pension overlays** — common among large defined-benefit plans in Europe and Japan — dynamically adjust equity exposure based on trailing vol.
- **CTA vol-control sleeves** within managed futures programs that size positions based on recent historical vol rather than fixed contracts.
- **Structured products** with embedded vol-control mechanisms, sold to retail investors as lower-risk equity exposure.

The aggregate AUM in strategies with some form of vol-targeting is estimated in the hundreds of billions to low trillions. The flows are mechanical, not discretionary. These funds don't buy on dips because valuations look cheap — they buy because vol fell and their model says exposure should increase. They don't sell because they're bearish — they sell because their risk budget requires it.

This is why vol spikes tend to be self-reinforcing in the short term. Higher realized vol triggers forced selling, which adds to realized moves, which triggers more selling. The unwind can happen faster than discretionary investors can react. The re-entry — once vol comes back down — is equally mechanical on the other side.

---

## The Term Structure of Realized Volatility

Realized vol is not a single number. It depends entirely on the window you measure it over. One-month trailing vol captures the recent regime; three-month vol reflects a longer horizon. The relationship between the two — the realized vol term structure — is a cleaner signal than either number in isolation.

**When 1-month realized vol is above 3-month:** The short end of the term structure is elevated. Recent moves have been larger than the medium-term average. For vol-targeting funds, the signal is clear — the trailing window they weight most heavily is showing elevated vol. Exposure gets cut.

**When 1-month realized vol is below 3-month:** The short end has calmed. The medium-term average is higher because a prior spike is still rolling through the 3-month window but has already exited the 1-month. This is the re-entry signal. The model says to add back exposure.

**The spread itself — 1mo minus 3mo — is the cleaner indicator than either level.** A strongly positive spread means the market is actively hot relative to its recent history: funds are reducing. A strongly negative spread means the hot period is fading from the calculation and funds are rebuilding. Near zero means transition or indecision.

This is structurally analogous to a yield curve. The short end reacts fast; the long end is slow. When the curve inverts — short above long — the near-term regime is elevated. When it steepens back — long above short — conditions are normalizing.

---

## The Tool

```cmd
python tools/spx_realized_vol.py
```

```text
Fetching ^GSPC from 2021-02-16...
  1339 trading days fetched  [2021-02-16 to 2026-06-15]

Latest values (as of 2026-06-15):
               AV_1mo     AV_3mo   Vol_Diff
Date
2026-06-09  12.901324  15.020755  -2.119431
2026-06-10  13.729014  15.142852  -1.413838
2026-06-11  15.032917  15.410869  -0.377951
2026-06-12  15.120760  15.412760  -0.292000
2026-06-15  15.991316  15.681758   0.309558

Chart saved -> .tmp/spx_rv_20260615.png
```

![SPX Realized Volatility: 1-Month vs 3-Month](../.tmp/spx_rv_20260615.png)

The top panel shows both vol measures alongside the SPX price level. The bottom panel is the spread — 1mo minus 3mo — filled blue when positive (short-term vol elevated, funds reducing exposure) and red when negative (short-term vol below medium-term, funds rebuilding exposure).

The five-year window makes the major regimes visible. The 2022 rate-shock period shows a sustained positive spread — persistent elevated near-term vol as the Fed hiked aggressively through the year. The post-2023 normalization shows a deeply negative spread: the 2022 spike rolling out of the 3-month window faster than it rolls out of the 1-month, creating a prolonged mechanical re-entry window for vol-targeting strategies. The April 2025 spike shows the same pattern at shorter duration — a fast positive spike, then a rapid return toward zero as the initial move faded.

---

## Current State

As of mid-June 2026, the spread sits just barely above zero — roughly +0.3 percentage points. One-month and three-month realized vol are nearly equal at around 16% annualized each.

The recent history tells the story better than the current print alone. The spread has oscillated through the April-June period as geopolitical developments drove sharp but short-lived vol spikes followed by equally sharp recoveries. The result is a 3-month window that absorbed significant volatility while the 1-month window has since calmed — but not by enough to produce the deeply negative spread that would signal clear mechanical re-entry.

This is the regime to be cautious about interpreting. Near-zero spread means vol-targeting funds are near neutral. Not forced sellers, but not aggressive buyers either. The spread could flip negative within days if calm persists — or flip back positive quickly if another geopolitical development drives a short vol spike. In fast-moving environments like this one, the current print matters less than the direction and duration of the next move.

---

## What to Watch

**Sustained positive spread (1mo above 3mo by 3+ percentage points for multiple weeks):** The unambiguous deleveraging signal. Not a one-day spike — a sustained regime where near-term vol persistently exceeds medium-term. The 2022 period in the chart is the clearest example. The implication isn't that markets will fall further, but that a structural mechanical bid is absent.

**Spread turning sharply negative after a spike:** The re-entry window. The prior spike is still in the 3-month window but has rolled out of the 1-month. The model says add exposure. This dynamic created a consistent bid through late 2023 and into 2024 as 2022 vol gradually rolled off the back end of the window.

**Rapid oscillation around zero — the current regime:** The least actionable environment for this signal. Small macro or geopolitical events can flip the spread positive or negative within a week. Vol-targeting flows are uncertain in both directions, and neither a structural bid nor a structural overhang is firmly in place.

The tool defaults to a 5-year lookback. Run it regularly when vol conditions are shifting — the full panel and the history of spread regimes does more explanatory work than the current number alone.

```cmd
python tools/spx_realized_vol.py --start 2020-01-01   # extend to include COVID spike
python tools/spx_realized_vol.py --out .tmp/custom.png
```

---

**Disclosure:** This analysis is for informational and educational purposes only. Nothing here constitutes investment advice, a solicitation, or a recommendation to buy or sell any security or derivative. All data is sourced from publicly available government and market data providers. Past relationships between implied and realized volatility do not guarantee future outcomes. DeltaTheta is an independent research publication.

---

If you want to follow the build, subscribe. If this has been useful and you'd like to help keep it going — coffee and API tokens are always appreciated.

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

— *DeltaTheta*
