# Workflow: Volatility Data — Realized vs Implied

## Objective

Fetch implied and realized volatility for major macro ETFs, compute the Volatility Risk Premium
(VRP = IV minus RV), and produce publication-quality charts. VRP is a genuine macro signal:
historically positive on average (options overprice realized moves), but it compresses or inverts
during stress events.

## Prerequisites

- `FRED_API_KEY` set in `.env`
- `yfinance` installed: `pip install yfinance`
- `fredapi`, `pandas`, `numpy`, `matplotlib`, `python-dotenv` installed

## Tools

- `tools/fred_fetch.py` — implied vol (CBOE indices via FRED)
- `tools/price_fetch.py` — realized vol (OHLC from yfinance) + options IV snapshot
- `tools/chart_macro.py` — visualization

## Ticker → Implied Vol Index Mapping

| ETF | Asset | FRED Series | Units | History |
| --- | --- | --- | --- | --- |
| SPY | S&P 500 | VIXCLS | Annualized % | 1990 |
| QQQ | NASDAQ-100 | VXNCLS | Annualized % | 2001 |
| GLD | Gold | GVZCLS | Annualized % | 2008 |
| USO | Crude Oil ETF | VXOCLS (discontinued Sept 2021) | Annualized % | 2007–2021 |
| XLE | Energy Sector | VXOCLS (proxy) | Annualized % | 2007 |
| TLT / IEF | Long Treasuries | VXTYN (historical) | Annualized % | 2003–2016 |

**TLT implied vol — two-source approach:**

- **2003–2016 (historical):** `VXTYN` on FRED — CBOE 10-Year Treasury Note Volatility Index.
  Discontinued but still queryable. Covers GFC (2008), taper tantrum (2013), rate normalization.
- **2016–present (current snapshot):** Use `--iv-snapshot` flag in `price_fetch.py` to pull
  current ATM 30-day IV from TLT's options chain. Point-in-time only — no historical series.
- **MOVE Index** (ICE BofA, the canonical "rates VIX"): NOT on FRED, requires paid subscription.

**Scope note:** `price_fetch.py` computes realized vol for any liquid ticker — ETFs, individual
stocks, sector ETFs. The CBOE index side is what limits the *historical* VRP comparison to the
instruments listed above. For any optionable ticker, current IV is available via `--iv-snapshot`.
The methodology applies broadly; the constraint is purely on the IV history side.

## Step 1 — Fetch Implied Vol (FRED)

```bash
# All CBOE vol indices + historical Treasury vol
python tools/fred_fetch.py \
    --series VIXCLS VXNCLS GVZCLS VXOCLS VXTYN \
    --start 2010-01-01 \
    --out .tmp/iv_cboe.csv

# VIX-only (longest history, S&P 500 focused)
python tools/fred_fetch.py --series VIXCLS --start 1990-01-01 --out .tmp/vix_history.csv
```

**Expected output:** CSV with date index, one column per series ID. VXTYN will be NaN from
~2016 onward (discontinued). VIX should show ~80+ in March 2020, ~30–40 in late 2022.

## Step 2 — Fetch Realized Vol (yfinance)

```bash
# All macro ETFs, both 20d and 30d windows
python tools/price_fetch.py \
    --tickers SPY QQQ GLD USO XLE TLT \
    --start 2010-01-01 \
    --window 20 30 \
    --out .tmp/rv_macro_etfs.csv

# SPY only, longer history to match VIX
python tools/price_fetch.py --tickers SPY --start 1993-01-01 --out .tmp/rv_spy.csv
```

**Expected output:** Long-format CSV with columns `date, ticker, close, rv_20d, rv_30d, pk_20d, pk_30d`.
First `window - 1` rows per ticker will be NaN (insufficient history). Parkinson (`pk_`) values
should be slightly lower than close-to-close (`rv_`) in quiet markets; both track each other closely.

**Volatility methods:**

- `rv_Nd` — Close-to-close: rolling std of log returns, annualized. Simple, widely understood.
- `pk_Nd` — Parkinson estimator: uses daily High/Low range. ~5x more statistically efficient.
  Formula: `sqrt( (1/(4×ln2)) × mean(ln(H/L)²) × 252 ) × 100`
  Prefer Parkinson for charts; note both in methodology disclosures.

## Step 3 — Compute VRP (Inline Pandas)

VRP = Implied Vol minus Realized Vol. A positive VRP means options priced in more vol than
subsequently realized (the norm). Inversion (negative VRP) signals stress or market dislocation.

```python
import pandas as pd

iv = pd.read_csv(".tmp/iv_cboe.csv", index_col="date", parse_dates=True)
rv = pd.read_csv(".tmp/rv_macro_etfs.csv", parse_dates=["date"])

# SPY vs VIX
spy = rv[rv["ticker"] == "SPY"].set_index("date")
vrp = iv[["VIXCLS"]].join(spy[["rv_20d", "pk_20d"]], how="inner").dropna()
vrp["vrp_rv20"]  = vrp["VIXCLS"] - vrp["rv_20d"]
vrp["vrp_pk20"]  = vrp["VIXCLS"] - vrp["pk_20d"]
vrp.to_csv(".tmp/vrp_spy_vix.csv")

# GLD vs GVZ
gld = rv[rv["ticker"] == "GLD"].set_index("date")
vrp_gld = iv[["GVZCLS"]].join(gld[["rv_20d", "pk_20d"]], how="inner").dropna()
vrp_gld["vrp_pk20"] = vrp_gld["GVZCLS"] - vrp_gld["pk_20d"]
vrp_gld.to_csv(".tmp/vrp_gld_gvz.csv")
```

**Date alignment note:** FRED and yfinance both use trading days but may differ by 1 day on
certain holidays. Use `how="inner"` in the join to keep only shared dates — this is safe.

**Timing note:** IV is forward-looking (VIX = expected vol over next 30 calendar days). RV is
backward-looking (trailing 20 trading days). The contemporaneous comparison (IV minus trailing RV)
is the practical market signal used here. Academic VRP studies sometimes use IV versus *subsequent*
realized vol — a different (and more precise) framing. Disclose this distinction in posts.

## Step 4 — Current IV Snapshot (any ticker)

When you need current implied vol without a FRED index — TLT, XLE, individual names:

```bash
# Point-in-time ATM IV from options chain
python tools/price_fetch.py --tickers TLT XLE SPY --iv-snapshot
```

Output: CSV and console showing current price, nearest 30-day expiry, ATM strike, and IV%.
**This is snapshot only — no historical series.** Use for "what is the market pricing right now."

## Step 5 — Charts

```bash
# Chart A: IV vs RV overlay (shows spread visually)
python tools/chart_macro.py \
    --csv .tmp/vrp_spy_vix.csv \
    --left VIXCLS rv_20d pk_20d \
    --title "S&P 500: Implied vs Realized Volatility" \
    --left-label "Volatility (%)" \
    --recessions \
    --out .tmp/vix_vs_rv_spy.png

# Chart B: VRP alone with fill-zero (stress inversions visible in red)
python tools/chart_macro.py \
    --csv .tmp/vrp_spy_vix.csv \
    --left vrp_pk20 \
    --fill-zero vrp_pk20 \
    --title "Volatility Risk Premium: VIX minus Parkinson RV (S&P 500)" \
    --left-label "VRP (%)" \
    --recessions \
    --out .tmp/vrp_spy.png
```

Chart B reuses the `--fill-zero` logic from `chart_macro.py` — the same mechanism used for yield
curve inversion. Positive VRP fills blue; negative (stress) fills red.

## Disclaimer Language for Posts

**Full disclosure block** — use whenever specific tickers appear in the post body:

> **Disclosure:** This analysis is for informational and educational purposes only. Nothing here
> constitutes investment advice, a solicitation, or a recommendation to buy or sell any security or
> derivative. All data is sourced from publicly available government and market data providers. Past
> relationships between implied and realized volatility do not guarantee future outcomes. DeltaTheta
> is an independent research publication.

**One-liner** — use for posts covering only macro indices with no specific ticker mentions:

> *This post is for informational purposes only and does not constitute investment advice.*

**Rule:** Use the full block whenever a post names specific tickers (SPY, QQQ, GLD, TLT, XLE, USO,
or any individual security). Use the one-liner for macro-only posts (VIX level, rate commentary,
yield curves, etc.).

## Notes and Constraints

- **Units:** CBOE indices are annualized %, `price_fetch.py` outputs annualized %. VRP subtraction
  is dimensionally consistent — no unit conversion needed.
- **yfinance adjusted prices:** `auto_adjust=True` corrects for splits and dividends. This is
  correct for return and vol calculations — do not disable.
- **Parkinson limitation:** Parkinson assumes no overnight gaps (uses intraday H/L only). For ETFs
  with after-hours moves (earnings, macro shocks), close-to-close RV captures overnight gaps that
  Parkinson misses. Both are informative; show both when space allows.
- **VXTYN discontinuation:** FRED still returns historical data through ~2016. Use for GFC-era
  and taper tantrum analysis. For current Treasury vol, use `--iv-snapshot` on TLT.
- **Individual stocks:** `price_fetch.py` computes RV for any liquid ticker. Historical IV for
  individual names is not freely available — yfinance options chains are snapshot-only. Do not
  attempt a historical RV vs IV comparison for individual stocks without a paid data source.

## Common Errors

| Error | Cause | Fix |
| --- | --- | --- |
| `No data for <ticker>` | Bad symbol or pre-IPO date range | Verify at finance.yahoo.com |
| `NaN for all pk columns` | H/L identical in data (yfinance gaps) | Filter rows where H==L before computing |
| Date gaps in VRP join | FRED/NYSE holiday mismatch | Use `how="inner"` — already in the recipe |
| `No options data for <ticker>` | Illiquid name or market closed | Retry during market hours; skip illiquid names |
| VXTYN all NaN after 2016 | Series discontinued | Expected — use snapshot for current reading |

## Next Steps After Fetching

- Visualize: `tools/chart_macro.py`
- Publish: `tools/substack_post.py` — include full disclaimer block in draft
- Layer with COT: overlay VIX COT positioning (`tools/cot_fetch.py --market VIX`) against VRP to
  see whether positioning aligns with premium compression
