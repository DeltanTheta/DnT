# COT Reports — Reading Futures Positioning

*DeltaTheta | Post 5 of the Build Series*

*Written by Claude with oversight.*

The yield curve tells you what the bond market expects. COT data tells you what traders are actually doing with their money.

The Commitments of Traders report is a weekly survey published by the CFTC — the Commodity Futures Trading Commission. Every futures market above a reporting threshold is included: equity index futures, Treasury futures, FX, volatility. For each market, the CFTC breaks down open interest by trader category. No other public data source gives you this level of visibility into who is positioned where across the major macro markets simultaneously.

It's also completely free. No API key. No subscription. Bulk CSV files downloaded directly from cftc.gov.

---

## The Format We're Using: TFF Disaggregated

The CFTC publishes COT data in several formats. We're using the **Traders in Financial Futures (TFF)** disaggregated report, which is the standard for financial markets. It breaks positioning into four categories:

**Leveraged Money**: Hedge funds, CTAs, and commodity trading advisors. These are trend-followers — they add to winning positions and cut losers. When Leveraged Money net positioning reaches a historical extreme in one direction, the trade is crowded.

**Asset Manager / Institutional**: Pension funds, mutual funds, endowments, and insurance companies. Longer time horizon, less reactive than hedge funds. Their positioning reflects structural allocation decisions, not tactical views.

**Dealer / Intermediary**: Banks, broker-dealers, and swap dealers. They're intermediaries by nature — their positioning reflects client flow and risk transfer, not directional conviction.

**Non-Reportable**: Positions too small to require reporting. Generally noise.

The signal lives in the Leveraged Money vs. Asset Manager relationship. Hedge funds are the most momentum-sensitive category — when they pile into a position, they're expressing a consensus directional view. When that view becomes extreme relative to history, it usually means most of the move has already happened and the position is vulnerable to any catalyst that forces unwinding.

Asset Managers move more slowly and are harder to squeeze. When their positioning diverges from Leveraged Money, it marks a difference in conviction between tactical and structural players — one of the more durable signals in the dataset.

---

## Markets We're Tracking

| Market | What It Tells You |
| --- | --- |
| E-Mini S&P 500 (CME) | Equity sentiment and hedge fund crowding |
| UST 10Y Note (CBOT) | Duration positioning — intermediate rate views |
| UST 2Y Note (CBOT) | Front-end positioning — Fed policy expectations |
| Euro FX (CME) | Dollar/euro regime and FX flows |
| VIX Futures (CBOE) | Volatility positioning — tail risk hedging vs. vol selling |

---

## The Code: cot_fetch.py

The tool is at `tools/cot_fetch.py`. Unlike `fred_fetch.py`, it downloads a ZIP file directly from cftc.gov — no authentication, no rate limits, no API key.

```bash
# Discover all available markets in the dataset
python tools/cot_fetch.py --list-markets --year 2024

# Pull positioning for our five core markets
python tools/cot_fetch.py --market "E-MINI S&P 500" "UST 10Y NOTE" "UST 2Y NOTE" "EURO FX" "VIX" --year 2024 --out .tmp/cot_macro_2024.csv
```

Output:

```
Loading COT data (2024)...
  Downloading: https://www.cftc.gov/files/dea/history/fut_fin_txt_2024.zip
  Cached -> .tmp\cot_txt_2024.zip
  Loaded 3,163 rows across 74 markets
  OK  'E-MINI S&P 500' -> E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE  (106 weeks)
  OK  'UST 10Y NOTE'   -> UST 10Y NOTE - CHICAGO BOARD OF TRADE  (53 weeks)
  OK  'UST 2Y NOTE'    -> UST 2Y NOTE - CHICAGO BOARD OF TRADE  (53 weeks)
  OK  'EURO FX'        -> EURO FX - CHICAGO MERCANTILE EXCHANGE  (53 weeks)
  OK  'VIX'            -> VIX FUTURES - CBOE FUTURES EXCHANGE  (53 weeks)

Saved 318 rows -> .tmp/cot_macro_2024.csv

      date       market_label    lev_net     am_net  dealer_net
2024-12-10        E-MINI S&P 500   271,441   -198,203    -83,441
2024-12-10          UST 10Y NOTE  -412,883    389,204     12,301
2024-12-10           UST 2Y NOTE   -98,441     91,330      6,884
2024-12-10           EURO FX      -74,212     38,104     31,209
2024-12-10               VIX          144    -14,904      8,549
```

Three things stand out in that snapshot.

**S&P 500**: Leveraged Money net long +271K, Asset Managers net short -198K. Hedge funds are positioned for continued equity upside; institutional investors are hedging against it. Whether that spread is extreme by historical standards is the question that requires context over time — but the directional setup is clear.

**10-Year Treasury**: Leveraged Money net short -413K, Asset Managers net long +389K. Hedge funds are positioned for higher yields (bond prices fall); institutional investors are buying duration. This is the classic "specs vs. real money" divergence in rates — often precedes a rates reversal once the consensus short gets squeezed.

**VIX**: Leveraged Money near flat (+144), Asset Managers net short -15K. Both categories selling volatility. In a trending equity market that tends to happen; it becomes a risk indicator when vol selling is extreme and equity positioning is simultaneously crowded long.

---

## Tool Design Notes

**ZIP caching.** The CFTC annual ZIPs are 2–4 MB each. The tool saves the downloaded file to `.tmp/cot_txt_{year}.zip` on first run. Subsequent calls reuse the cached file — `--zip .tmp/cot_txt_2024.zip` makes iteration fast.

**Cross-rate filtering.** CFTC market names for FX include both outright contracts ("EURO FX") and cross-rates ("EURO FX/BRITISH POUND XRATE"). The tool prefers outright contracts over cross-rates when the query matches both, so `--market "EURO FX"` returns EUR/USD positioning, not EUR/GBP.

**74 markets in the TFF dataset.** The file includes equity indices (S&P, NASDAQ, Russell), Treasury futures across the curve (2Y, 5Y, 10Y, 30Y), G10 FX, crypto (Bitcoin, Ethereum), VIX, and sector ETF futures. `--list-markets` shows the full list with exact names.

---

## What's Next

COT data as a weekly snapshot is a starting point. The analytical layer comes when you normalize positioning against its historical range — what does -412K Leveraged Money short in 10-Year Treasuries look like relative to the prior five years? Is it at the 90th percentile of bearishness or the median?

That context is what turns a positioning number into a signal. Next post builds that visualization.

Next post: **COT Visualization — Positioning Over Time**. We'll chart Leveraged Money vs. Asset Manager net positioning historically, add a percentile band to mark extremes, and produce the first multi-panel positioning dashboard from the pipeline.

If you want to follow the build, subscribe. If this has been useful and you'd like to help keep it going — coffee and API tokens are always appreciated.

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

— *DeltaTheta*
