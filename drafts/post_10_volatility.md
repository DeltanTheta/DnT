# Volatility — What the Options Market Is Pricing as Risk

*DeltaTheta | Post 10 of the Build Series*

*Written by Claude with oversight.*

Every macro data release gets parsed for what it means for rates. But there is a parallel market running at all times that prices uncertainty directly — not through yields or spreads, but through options. Implied volatility is the options market's real-time answer to the question: *how much do we expect this asset to move?*

When implied vol diverges from how much the asset is actually moving, that gap is information. It is called the Volatility Risk Premium, and it is one of the cleaner macro signals we have access to with entirely free data.

This post builds the infrastructure to measure it systematically.

---

## Two Kinds of Volatility

**Realized volatility** measures what already happened. Take daily price returns over some trailing window, compute the standard deviation, annualize it. If SPY moved an average of roughly 0.9% per day over the last 20 trading days, that annualizes to about 14%. That is realized vol — backward-looking, precise, undisputed.

**Implied volatility** measures what the options market expects to happen. It is the volatility level implied by current options prices. If SPY call and put options are priced such that the market is pricing in an average daily move of roughly 1.2% over the next 30 days, the implied vol is around 19%. That is implied vol — forward-looking, a market consensus, and always somewhat uncertain.

The CBOE publishes official implied vol indices for major asset classes. The VIX is the most famous — it measures the 30-day implied volatility of the S&P 500, derived from a basket of SPX options across strikes, not just at-the-money. Similar indices exist for the NASDAQ-100 (VXN), Gold (GVZ), and Crude Oil (OVX). All of them are available daily through FRED.

For realized vol, we use the **Parkinson estimator** — a method that uses each day's high and low prices rather than just closing prices. The formula is:

```
σ_Parkinson = sqrt( (1 / (4 × ln2)) × mean(ln(H/L)²) × 252 ) × 100
```

The constant `1/(4×ln2) ≈ 0.36` comes from the derivation assuming Brownian motion with no drift. Parkinson uses more information per day (intraday range vs. close-to-close change) and produces more statistically efficient estimates — roughly 5x lower variance for the same sample size. We still compute close-to-close vol for comparison, but Parkinson is what goes in the VRP calculation.

---

## The Volatility Risk Premium

The **Volatility Risk Premium (VRP)** is simply: implied vol minus realized vol.

```
VRP = IV − RV
```

VRP is historically positive for most assets. Options are almost always priced slightly higher than what subsequently realized vol turns out to be. The reasons are structural:

- **Option sellers demand a premium** for taking on exposure to tail events. Even in a calm environment, the next event is unknown.
- **Demand for protection is persistent.** Institutions hedge portfolios with puts regardless of market conditions. This consistent demand bids up options prices.
- **The distribution of realized vol is right-skewed.** Most of the time vol is low, but when it spikes it spikes hard. Option buyers are paying for the rare but severe move.

The long-run average VRP for SPY vs. VIX is approximately +4 to +6 percentage points. The VIX typically runs 4–6 points above the trailing 20-day realized vol of the S&P 500.

**When VRP compresses toward zero**, the options market is pricing in approximately as much movement as is already being realized. This happens during trending regimes — when realized vol is elevated and catching up to the implied vol priced in at the start of the period.

**When VRP inverts (goes negative)**, realized vol is *exceeding* what was priced into options. This is the stress signal. It means the market underpriced the actual move — usually during sudden dislocations where realized vol spikes faster than implied vol adjusts. The COVID crash in March 2020 is the textbook example: VIX hit 85 but daily realized moves were briefly higher still.

---

## The Code

Two tools work together. First, implied vol from FRED:

```cmd
python tools/fred_fetch.py --series VIXCLS VXNCLS GVZCLS VXOCLS --start 2010-01-01 --out .tmp/iv_cboe.csv
```

```text
Fetching 4 series from FRED...
  OK  VIXCLS               CBOE VIX — S&P 500 Implied Vol  (4148 observations)
  OK  VXNCLS               CBOE VXN — NASDAQ-100 Implied Vol  (4148 observations)
  OK  GVZCLS               CBOE GVZ — Gold Implied Vol  (4148 observations)
  OK  VXOCLS               CBOE OVX — Crude Oil ETF Implied Vol  (3912 observations)

Saved 4148 rows x 4 cols -> .tmp/iv_cboe.csv
```

Then realized vol from price history — plus options chain snapshots for tickers without a CBOE index (XLE, TLT):

```cmd
python tools/price_fetch.py --tickers SPY QQQ GLD USO XLE TLT --start 2010-01-01 --window 20 30 --out .tmp/rv_macro_etfs.csv
```

```text
Fetching OHLC data for: SPY, QQQ, GLD, USO, XLE, TLT
  OK  SPY     3902 trading days  [2010-01-04 to 2026-06-11]
  OK  QQQ     3902 trading days  [2010-01-04 to 2026-06-11]
  OK  GLD     3902 trading days  [2010-01-04 to 2026-06-11]
  OK  USO     3902 trading days  [2010-01-04 to 2026-06-11]
  OK  XLE     3902 trading days  [2010-01-04 to 2026-06-11]
  OK  TLT     3902 trading days  [2010-01-04 to 2026-06-11]

Saved 23412 rows x 6 cols -> .tmp/rv_macro_etfs.csv
```

Or run the snapshot tool to get everything in one shot — current IV, trailing RV, and the color-shaded table PNG:

```cmd
python tools/vol_snapshot.py
```

```text
Fetching CBOE implied vol from FRED (3 series)...
  OK  VIXCLS     19.44%  (as of 2026-06-11)
  OK  VXNCLS     30.44%  (as of 2026-06-11)
  OK  GVZCLS     28.33%  (as of 2026-06-11)

Fetching options chain IV for: USO, XLE, TLT...
  OK  USO        50.34%  (ATM options, exp 2026-07-10)
  OK  XLE        27.59%  (ATM options, exp 2026-07-10)
  OK  TLT         8.79%  (ATM options, exp 2026-07-10)

Fetching realized vol (Parkinson 20d) via yfinance...
  OK  SPY        RV (Parkinson 20d) = 12.61%
  OK  QQQ        RV (Parkinson 20d) = 20.39%
  OK  GLD        RV (Parkinson 20d) = 17.08%
  NOTE CL=F       3 roll-gap day(s) filtered
  OK  CL=F       RV (Parkinson 20d) = 53.31%
  OK  XLE        RV (Parkinson 20d) = 22.01%
  OK  TLT        RV (Parkinson 20d) = 6.60%

Table saved -> .tmp/vol_snapshot_20260612.png
```

One detail worth flagging in the output: crude oil realized vol uses `CL=F` (WTI continuous front-month futures) rather than USO price history. USO is an ETF that rolls monthly from front-month to the next contract — in contango markets, this creates a small but real negative yield that suppresses the ETF's price movements relative to actual crude. For measuring what WTI has actually been doing, the continuous futures contract is the cleaner signal. USO options are still used for implied vol, since free historical IV data for CME crude options isn't available and USO's options market is liquid.

The `NOTE` line shows that three contract roll-expiry days were detected and filtered from the Parkinson calculation. On those days, Yahoo Finance's High/Low spread reflects the price difference between expiring and new contracts, not an actual intraday move — including them would artificially inflate the realized vol estimate.

---

## Current Snapshot

![Volatility Snapshot Table](../.tmp/vol_snapshot_20260612.png)

The VRP column is color-shaded: **green** means options are pricing a normal premium above realized moves. **Yellow** means the premium is thin — the market is pricing in close to what it has already been doing. **Red** means stress — realized vol is exceeding what was priced into options.

The first thing to notice is that every row is green — all six assets show a positive VRP, some substantially so. This isn't a calm market that's been fairly priced. It's a market pricing elevated uncertainty premiums across multiple asset classes simultaneously. That is the story.

**SPY (S&P 500) — VRP +6.8%.** Realized vol at 12.6% is actually low — below the long-run average for the S&P 500. The VIX at 19.4% isn't extreme, but the spread between them is wide. The equity market has been moving calmly, but options buyers are paying for forward uncertainty: inflation still above target, Fed on hold, tariff pass-through still playing out. The calm in realized vol is a recent artifact; the VIX is pricing the environment, not just the last 20 days.

**QQQ (NASDAQ-100) — VRP +10.1%.** The most expensive index in terms of premium. VXN at 30.4% against a realized vol of 20.4% means NASDAQ options are priced at nearly 1.5x recent actual moves. The NASDAQ 100's top-10 concentration (Apple, NVIDIA, Microsoft, Meta, Amazon make up roughly 45% of the index) creates persistent event-risk demand — any one of those names reporting, making a capital allocation announcement, or entering a regulatory dispute reprices the whole index. A 10-point VRP is structurally elevated, not a temporary anomaly.

**GLD (Gold) — VRP +11.2%.** This is the most striking reading in the table. Gold has been moving at 17% annualized — that is not a quiet market. But the options market is pricing 28%, nearly double the recent realized vol. GVZ at 28.3% is historically high for gold. In the current environment — dollar credibility uncertainty, central bank accumulation, tariff-driven safe haven demand — the options market is treating gold as a tail-risk hedge and pricing accordingly. The premium isn't irrational; it reflects the scenario distribution. If tariff escalation accelerates or the dollar weakens sharply, gold's actual moves could easily reach 28%. The options market is being paid to provide that insurance.

**USO (Crude Oil) — VRP -3.0%.** The only red cell in the table, and the most important reading. Crude oil realized vol — measured from WTI continuous futures (CL=F) rather than USO to avoid ETF roll drag — is running at 53.3% annualized. The options market, using USO as the IV proxy, is pricing only 50.3%. The options market has been *underpricing* what crude has actually been doing.

A negative VRP doesn't mean options are cheap in absolute terms — 50% implied vol is enormous. It means the market hasn't fully caught up to realized moves. In the current environment, WTI has been whipsawed by competing forces: tariff-driven demand destruction fears, OPEC+ supply decisions, and geopolitical risk. The actual daily moves have been exceeding what options were pricing at the start of each 30-day window. That's the stress signal.

Note on methodology: the IV here comes from USO options (the best free proxy available — the CBOE OVX index was discontinued in 2021, and CME crude options data isn't freely accessible). The RV comes from CL=F continuous futures. The two aren't perfectly apples-to-apples, but the directional signal is valid: crude price vol is running hot relative to what options were priced for.

**XLE (Energy Sector) — VRP +5.6%.** The sector ETF is more contained than crude itself — XLE diversifies across majors, pipelines, and services companies, which smooths idiosyncratic commodity exposure. The premium is elevated but not extreme. XLE's story is the same as USO's at a lower amplitude.

**TLT (Long Treasury) — VRP +2.2%.** The outlier. Treasury bond options are almost fairly priced relative to recent moves — the thinnest premium in the group by a significant margin. TLT realized vol at 6.6% is low, and the options market is only pricing 8.8%, barely more. This is surprising given the macro backdrop: inflation running above target, the Fed stuck, fiscal deficits expanding. Long bonds *should* be pricing more uncertainty. Two possible explanations: either the market genuinely believes the rate path is anchored and TLT won't move much from here, or options sellers have crowded into the trade and suppressed IV. A VRP this thin on long bonds is worth watching — a policy shock or inflation resurgence could see TLT realized vol quickly exceed its implied level, producing a brief negative VRP inversion.

---

## The VRP as a Macro Signal

VRP is useful in two distinct ways:

**Cross-sectional:** Compare VRP across asset classes at a point in time. When equities have a normal VRP but crude has an inverted or near-zero VRP, the options market is saying something different about oil than about stocks. That divergence can reflect regime transitions — a commodity shock that hasn't yet fed into equity pricing, for instance.

**Time-series:** Track VRP for a single asset over time. A consistently positive VRP is the baseline. Persistent compression toward zero signals uncertainty about near-term direction — the options market is no longer confident it is overpricing moves. An inversion is the stress signal. You don't need to time the exact inversion — the trend from high VRP to near-zero to negative is the progression worth watching.

One important nuance: because IV is *forward-looking* (the next 30 calendar days) and RV is *backward-looking* (the past 20 trading days), the two measures are not perfectly aligned in time. What we are computing is a contemporaneous comparison — the market's current expectation vs. what the market just did. Academic work sometimes defines VRP as IV minus *subsequent* realized vol, which requires waiting 30 days to compute. For live monitoring, the contemporaneous comparison is the practical version, and it is what the chart shows.

---

## The Full Time-Series

To see how VRP has evolved and where it stood during past stress events, use `chart_macro.py` with the VRP fill-zero option:

```cmd
python tools/chart_macro.py --csv .tmp/vrp_spy_vix.csv --left vrp_pk20 --fill-zero vrp_pk20 --title "Volatility Risk Premium: VIX minus Parkinson RV (S&P 500)" --left-label "VRP (%)" --recessions --out .tmp/vrp_spy.png
```

This uses the same fill-zero mechanism as the yield curve inversion chart — green fill when VRP is positive, red when it inverts. The chart makes the stress events visually immediate: March 2020, August 2015, the Q4 2018 drawdown. All of them show brief VRP inversion where realized vol overshot what options had priced in.

The methodology applies to any liquid ticker or ETF. The limitation is on the implied vol side — CBOE publishes indices for the major asset classes listed above. For individual names or sector ETFs, the `--iv-snapshot` flag in `price_fetch.py` pulls current ATM IV from the options chain. That gives you a real-time reading for any optionable security. What it doesn't give you is historical IV to construct the full time-series comparison — that requires a paid data source.

---

## What's in the Data

The series we now have access to:

| Series / Ticker | Source | Description | Frequency |
| --- | --- | --- | --- |
| VIXCLS | CBOE via FRED | S&P 500 30-day implied vol | Daily, since 1990 |
| VXNCLS | CBOE via FRED | NASDAQ-100 implied vol | Daily, since 2001 |
| GVZCLS | CBOE via FRED | Gold ETF implied vol | Daily, since 2008 |
| VXOCLS | CBOE via FRED | Crude Oil ETF implied vol | Daily, since 2007 |
| VXTYN | CBOE via FRED | 10-Year Treasury implied vol | Daily, 2003–2016 |
| SPY/QQQ/GLD/USO/XLE/TLT | yfinance | Daily OHLC for RV calculation | Daily |

---

## Methodology Note

**Realized vol methods:**
- *Close-to-close* (`rv_Nd`): rolling standard deviation of daily log returns, annualized. Simple and widely understood.
- *Parkinson estimator* (`pk_Nd`): uses daily High/Low range. Approximately 5x more statistically efficient. Used in the VRP calculation.

**VRP timing:** IV is forward-looking (expected vol over the next 30 calendar days). RV is backward-looking (trailing 20 trading days). The contemporaneous comparison is the standard live monitoring approach; it differs from the academic definition of VRP which compares current IV to subsequent realized vol.

**TLT implied vol:** The CBOE TYVIX index (VXTYN on FRED) was discontinued in 2016. For historical analysis through 2016, VXTYN is available via `fred_fetch.py`. For current readings, the options chain snapshot (`price_fetch.py --iv-snapshot`) provides ATM IV. The MOVE index — the canonical rates VIX — requires a paid ICE subscription and is out of scope for this pipeline.

---

**Disclosure:** This analysis is for informational and educational purposes only. Nothing here constitutes investment advice, a solicitation, or a recommendation to buy or sell any security or derivative. All data is sourced from publicly available government and market data providers. Past relationships between implied and realized volatility do not guarantee future outcomes. DeltaTheta is an independent research publication.

---

If you want to follow the build, subscribe. If this has been useful and you'd like to help keep it going — coffee and API tokens are always appreciated.

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

— *DeltaTheta*
