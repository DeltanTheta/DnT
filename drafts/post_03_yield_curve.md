# The Yield Curve — What It Measures, Why It Belongs, and the Code to Pull It

*DeltaTheta | Post 3 of the Build Series*

*Written by Claude with oversight.*

Post 2 built the scaffolding. This post uses it.

The first indicator we're ingesting is the yield curve — specifically the relationship between the 2-year and 10-year Treasury yields and the spread between them. Before we get to the code, it's worth being precise about what we're actually measuring and why this goes into the pipeline before anything else.

---

## What the Yield Curve Measures

A yield curve plots Treasury yields across maturities: 1 month, 3 months, 2 years, 10 years, 30 years. The version that carries most of the signal is the simplest — the difference between long-term and short-term yields.

When long-term yields exceed short-term yields, the curve slopes upward. That's normal. It reflects compensation for time and uncertainty: you expect more return for locking up capital longer, and more time means more potential for things to go wrong.

When short-term yields rise above long-term yields, the curve inverts. That's abnormal. It means the market expects short-term rates to fall in the future — which is what happens when economic growth slows and the Fed eventually cuts rates in response.

The two rates that define most of the signal:

**2-Year Treasury (DGS2)**: Anchored to Fed policy expectations over the next two years. If the market expects hikes, the 2-year rises. If cuts are being priced in, the 2-year falls. It's the most direct market-based measure of where monetary policy is headed.

**10-Year Treasury (DGS10)**: Driven by long-run growth and inflation expectations, plus a term premium for holding duration. It moves more slowly and is less sensitive to near-term Fed moves.

The spread between them — the 2s10s — is the gap between where we're going (short-term policy path) and where we expect to end up (long-run equilibrium). A positive spread means the market believes conditions will remain robust enough to justify elevated rates. A negative spread means the market has already priced in a reversal.

---

## Why Inversion Precedes Recessions

Every U.S. recession since the 1960s has been preceded by an inverted yield curve. That's not a statistical accident — there's a mechanism.

Banks borrow short and lend long. They take deposits (short-term liabilities) and make loans (long-term assets). When the curve inverts, their net interest margin — the spread between what they earn and what they pay — compresses or goes negative. Credit creation slows. Lending standards tighten. Businesses that depend on short-term borrowing face higher rates than long-term projects can justify.

Inversion doesn't cause the recession directly. It reflects expectations that monetary policy has tightened enough to slow the economy, and it accelerates the slowdown by constraining the credit channel.

The lag is variable — typically 6 to 18 months from initial inversion to recession onset. That lag is long enough that most practitioners discount the signal until it's obvious, which is part of what makes it useful for macro thinking. You're not timing the week. You're classifying the regime.

The signal isn't infallible. The 2022–2024 inversion was the deepest and most sustained in decades — and a recession, by conventional definition, never arrived. The Fed tightened aggressively, the curve inverted sharply, credit standards tightened, and yet the labor market and consumer spending held. Whether that represents a genuine soft landing or a recession that was deferred rather than avoided is still being debated. What it does confirm is that inversion is a necessary-but-not-sufficient condition. It raises the probability of recession; it doesn't guarantee one. Use it to tilt your priors, not to call the outcome.

---

## Two Spreads We Track

**The 2s10s (T10Y2Y)**: The benchmark spread. Most quoted by practitioners and financial media. The 2-year is policy-sensitive; the 10-year is growth-sensitive. The spread captures "how far has current policy deviated from long-run conditions."

**The 10Y-3M (T10Y3M)**: The spread between the 10-year and the 3-month bill. Research from the New York Fed — particularly work by Arturo Estrella — found this spread has stronger statistical properties as a recession predictor than the 2s10s. The 3-month bill is even more tightly anchored to the current Fed funds rate than the 2-year. When this spread inverts, the signal-to-noise ratio is higher.

In practice, we track both. They don't always move together, and divergences between them are informative.

---

## The Code: fred_fetch.py

The tool is at `tools/fred_fetch.py`. It does one job: accept a list of FRED series IDs and return a clean CSV.

```python
def fetch(series_ids: list[str], start: str = "2000-01-01", end: str | None = None) -> pd.DataFrame:
    api_key = os.getenv("FRED_API_KEY")
    fred = Fred(api_key=api_key)
    frames = {}

    for sid in series_ids:
        s = fred.get_series(sid, observation_start=start, observation_end=end)
        s.name = sid
        frames[sid] = s
        label = KNOWN_SERIES.get(sid, sid)
        print(f"  OK  {sid:<20} {label}  ({len(s)} observations)")

    return pd.DataFrame(frames)
```

That's the core. The full script wraps this in argument parsing, error handling, and output path logic — but the job is to call `fred.get_series()` for each ID, concatenate the results into a single DataFrame, and write it to CSV.

A few design decisions worth noting.

**One DataFrame, all series.** We could write each series to a separate file. Instead, everything goes into one CSV with date as the index and series IDs as column names. Downstream joins are trivial, file count stays manageable, and any charting tool can consume it without normalization.

**Named series dictionary.** The script maintains a `KNOWN_SERIES` dict mapping IDs to readable names. This is documentation embedded in code. When you see `DGS2` in a CSV two months from now, you can check the script and know it's the 2-Year Treasury yield. It also makes errors more legible when a series ID is wrong.

**SSL context workaround.** Python 3.14 on Windows ships without bundled CA certificates, which breaks HTTPS connections to FRED. We patch the SSL context at process startup. It's a narrow exception for a known platform quirk, documented in the code, and scoped to this script only.

To pull the yield curve data:

```bash
python tools/fred_fetch.py --series DGS2 DGS10 T10Y2Y T10Y3M --start 2000-01-01
```

Output:

```
Fetching 4 series from FRED...
  OK  DGS2                 Treasury 2-Year Yield  (6651 observations)
  OK  DGS10                Treasury 10-Year Yield  (6651 observations)
  OK  T10Y2Y               10Y-2Y Spread (Yield Curve)  (6651 observations)
  OK  T10Y3M               10Y-3M Spread  (6651 observations)

Saved 6651 rows x 4 cols -> .tmp/fred_DGS2_DGS10_T10Y2Y_20260612.csv

              DGS2   DGS10  T10Y2Y  T10Y3M
date
2026-06-06    3.95    4.41    0.46    0.14
2026-06-09    3.98    4.44    0.46    0.13
2026-06-10    3.97    4.43    0.46    0.13
2026-06-11    3.96    4.42    0.46    0.12
2026-06-12    3.94    4.40    0.46    0.12
```

6,651 daily observations from January 2000 through today — 26 years of yield curve history — fetched in under two seconds.

---

## What the Data Says Right Now

As of today, the 2s10s is around +46 basis points — positive but modest. The curve has re-steepened after the inversion that ran from mid-2022 through late 2024, one of the most sustained inversions in the historical record. The 10Y-3M is narrower at around +12 basis points; 3-month rates haven't come down as far as 2-year rates yet, reflecting the staggered pace of Fed cuts working through the short end.

A steepening after a prolonged inversion can mean two things: the market is confident growth is reaccelerating (bearish steepener — long rates rise faster than short rates fall), or the market is pricing in emergency cuts because something broke (bull steepener — short rates collapse). Which one it is shapes everything downstream — credit spreads, equity factor exposure, dollar positioning.

Right now the pattern looks more like a gradual normalization than a distress signal. But that's a regime judgment, not a data-fetch result. The data fetch just gives us the input.

---

## What the Chart Looks Like

The visualization is produced by `tools/chart_macro.py`. Here's the command that generates the publication chart:

```cmd
python tools/chart_macro.py --csv .tmp/fred_DGS2_DGS10_T10Y2Y_20260612.csv --left DGS2 DGS10 --right T10Y2Y --fill-zero T10Y2Y --recessions --title "US Yield Curve: 2Y vs 10Y and Spread (2000-2026)" --out .tmp/yield_curve_2000_2026.png
```

The `--fill-zero` flag shades the spread area blue when the curve is normal and red when inverted. `--recessions` fetches NBER recession dates from FRED and adds gray bands. The result is a chart where you can see the 2001, 2008, and 2020 recessions following inversions at a glance — the predictive relationship visible without calculation.

![US Yield Curve 2000–2026](../.tmp/yield_curve_2000_2026.png)

Next post covers `chart_macro.py` in full: the dual-axis layout, how the recession shading works, and the design decisions behind the color scheme and annotation logic.

---

Next post: **Charting the Yield Curve — Building the Visualization Layer**. We'll walk through `chart_macro.py`, explain how the dual-axis layout and recession shading are constructed, and ship the first publication-quality chart from the pipeline.

If you want to follow the build, subscribe. If this has been useful and you'd like to help keep it going — coffee and API tokens are always appreciated.

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

— *DeltaTheta*
