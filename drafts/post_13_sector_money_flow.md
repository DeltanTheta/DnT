# Sector Money Flow: Where the 15-Day Pressure Is Right Now

*DeltaTheta | Post 13 of the Build Series*

*Written by Claude with oversight.*

Price tells you where something has been. Volume tells you how much conviction was behind it. Money flow combines both: it measures whether volume is clustering on up-moves or down-moves within each bar, and aggregates that signal over a rolling window. The result is a pressure reading — not a price level — that indicates whether buyers or sellers have had the structural edge over the period.

This post introduces the sector money flow tool built into the pipeline, walks through the current 15-day snapshot across the 11 major S&P 500 sectors plus fixed income and gold proxies, and reads what the current pressure distribution says about how capital is positioned right now.

---

## What We're Measuring

The metric is **Chaikin Money Flow (CMF)**, computed over a 15-day rolling window. The formula per bar:

```
MFM = ((Close - Low) - (High - Close)) / (High - Low)
MFV = MFM × Volume
CMF = sum(MFV, 15) / sum(Volume, 15)
```

The Money Flow Multiplier (MFM) ranges from −1 to +1: +1 means the bar closed at its high on full volume, −1 means it closed at its low. Weighting by volume and rolling over 15 days gives a normalized pressure reading across the window.

**One important caveat before reading anything below:** these readings are measurements of specific ETF tickers, not the full sector market cap. XLF is not "all financial stocks." TLT is not "all fixed income." They are liquid proxies that track the respective asset class closely, but the CMF reading you see is the exact flow into that ticker — indicative of broader directional pressure, not a precise accounting of the sector.

---

## The Proxy Map

| Ticker | Asset | What It Proxies |
|--------|-------|-----------------|
| XLB | Materials Select SPDR | S&P 500 Materials sector |
| XLC | Communication Services Select SPDR | S&P 500 Comm Services sector |
| XLE | Energy Select SPDR | S&P 500 Energy sector |
| XLF | Financial Select SPDR | S&P 500 Financials sector |
| XLI | Industrial Select SPDR | S&P 500 Industrials sector |
| XLK | Technology Select SPDR | S&P 500 Technology sector |
| XLP | Consumer Staples Select SPDR | S&P 500 Consumer Staples sector |
| XLRE | Real Estate Select SPDR | S&P 500 Real Estate sector |
| XLU | Utilities Select SPDR | S&P 500 Utilities sector |
| XLV | Health Care Select SPDR | S&P 500 Health Care sector |
| XLY | Consumer Discretionary Select SPDR | S&P 500 Consumer Discretionary sector |
| TLT | iShares 20+ Year Treasury ETF | Long-duration fixed income proxy |
| GLD | SPDR Gold Shares | Gold proxy |

---

## The Tool

The `sector_money_flow.py` script fetches daily OHLCV data for all 13 tickers via yfinance, computes 15-day CMF for each, outputs the full time series to `.tmp/`, and optionally generates a bar chart of the latest snapshot.

```
python tools/sector_money_flow.py --chart
```

```
Fetching OHLCV for 13 tickers...
  OK  XLB    365 trading days  [2025-01-02 to 2026-06-17]
  OK  XLC    365 trading days  [2025-01-02 to 2026-06-17]
  OK  XLE    365 trading days  [2025-01-02 to 2026-06-17]
  OK  XLF    365 trading days  [2025-01-02 to 2026-06-17]
  OK  XLI    365 trading days  [2025-01-02 to 2026-06-17]
  OK  XLK    365 trading days  [2025-01-02 to 2026-06-17]
  OK  XLP    365 trading days  [2025-01-02 to 2026-06-17]
  OK  XLRE   365 trading days  [2025-01-02 to 2026-06-17]
  OK  XLU    365 trading days  [2025-01-02 to 2026-06-17]
  OK  XLV    365 trading days  [2025-01-02 to 2026-06-17]
  OK  XLY    365 trading days  [2025-01-02 to 2026-06-17]
  OK  TLT    365 trading days  [2025-01-02 to 2026-06-17]
  OK  GLD    365 trading days  [2025-01-02 to 2026-06-17]

Computing 15-day CMF...

Saved 365 rows x 13 cols -> .tmp/sector_cmf_20260617.csv

--- Latest 15-day CMF snapshot (2026-06-17) ---
ticker                  label  cmf_15d
   TLT   Fixed Income (proxy)   0.1495
   XLF             Financials   0.1418
   XLK             Technology   0.0944
   XLB              Materials   0.0581
   XLI            Industrials   0.0486
   XLC          Comm Services  -0.0658
   XLE                 Energy  -0.1268
   XLV            Health Care  -0.1282
   XLU              Utilities  -0.1600
   XLP       Consumer Staples  -0.1760
  XLRE            Real Estate  -0.1940
   XLY Consumer Discretionary  -0.1988
   GLD           Gold (proxy)  -0.2022

Chart saved -> .tmp/sector_cmf_chart_20260617.png
```

---

## The Current Snapshot

![Sector Money Flow — 15-Day CMF, June 17 2026](../.tmp/sector_cmf_chart_20260617.png)

### What's Seeing Inflows

**Fixed income (TLT) and Financials (XLF) are leading.** This pairing is worth pausing on — in a rising-rate environment, these two tend to move in opposite directions, since higher rates compress bond prices while initially helping net interest margins. Both posting positive CMF simultaneously is more consistent with a rate-*cut* expectation environment: falling rates lift bond prices (TLT inflow) while the prospect of easier financial conditions supports financial sector sentiment (XLF inflow). It could also reflect a flight-to-quality bid for Treasuries alongside a broader risk-on lift in equities — the correlation matrix from post 12 showed exactly this: a positive equity-duration correlation regime.

**Technology (XLK) is solidly positive.** Growth-sensitive, long-duration in its valuation profile, and historically the first equity sector to reprice when rate expectations shift lower. XLK joining TLT in positive territory is consistent with a rate-sensitive risk-on move rather than pure cyclical rotation.

**Materials (XLB) and Industrials (XLI) are mildly positive.** These are cyclical sectors — they tend to benefit from growth expectations. Their presence in positive territory, though well below financials and tech, suggests the inflow picture isn't purely defensive or rate-driven. There's some growth-cycle support in the read.

### What's Seeing Outflows

**The sharpest outflows are in the defensive yield plays.** Consumer Staples (−0.18), Utilities (−0.16), and Real Estate (−0.19) are in the bottom tier. These three sectors are often treated as bond proxies — investors hold them for their yield and stability characteristics. When rates fall or risk appetite rises, capital tends to rotate out of these into higher-beta areas. The CMF signal here is consistent with that rotation: money is leaving the low-volatility yield substitutes.

**Consumer Discretionary (XLY) is near the bottom at −0.20.** This is the most structurally interesting outlier. In a pure risk-on environment you might expect discretionary to benefit — but discretionary is also highly sensitive to consumer credit conditions and wage expectations. Its weakness alongside staples outflow could reflect sector-specific concern about consumer balance sheets rather than a macro-risk-off read.

**Gold (GLD) is the weakest at −0.20.** Gold's outflow while fixed income is seeing inflows is a meaningful signal. When both move in the same direction (both up or both down), the common driver is usually macro uncertainty or inflation expectations. When they diverge — bonds up, gold down — it tends to reflect falling real rates without the fear premium: a "soft landing" or "rates falling for the right reasons" read. Gold is less useful as a hedge when nominal rates are falling because the monetary system is calming, not breaking.

**Energy (XLE) and Health Care (XLV) are in moderate outflow.** Energy has its own supply/demand drivers and tends to be driven more by crude pricing than macro positioning. Health care is a defensive sector with a different character than staples or utilities — its outflow here may be more idiosyncratic than regime-driven.

---

## Bottom Line

The 15-day CMF snapshot is telling a coherent story: capital is rotating into rate-sensitive growth assets (fixed income, tech, financials) and out of defensive yield substitutes (staples, utilities, real estate) and gold. That's the profile of a market pricing in falling rates without a fear premium — falling rates as a *tailwind*, not a warning sign.

The sectors seeing inflows (TLT, XLF, XLK) are consistent with the positive equity-duration correlation regime identified in the correlation matrix. The sectors seeing outflows (XLP, XLU, XLRE) are the ones that benefit least — or get actively rotated out of — when that regime holds.

What to watch: if gold flips positive while TLT stays positive, that changes the read toward uncertainty rather than soft-landing. If XLY recovers while XLP continues to bleed, that would suggest the consumer picture is more rotation than stress.

---

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

— *DeltaTheta*
