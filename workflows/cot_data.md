# Workflow: CFTC COT Data Ingestion

## Objective

Download the CFTC Commitments of Traders (COT) legacy report and extract net positioning by trader category (Non-Commercial, Commercial) for specified futures markets.

## Prerequisites

- `requests`, `pandas` installed
- No API key required — CFTC publishes bulk CSV/ZIP files publicly

## Tool

`tools/cot_fetch.py`

## Inputs

| Parameter | Required | Description |
| --- | --- | --- |
| `--market` | Yes (or --list-markets) | Market name fragment(s), space-separated |
| `--year` | No | Year to fetch (default: 2024) |
| `--zip` | No | Path to cached local ZIP (skips re-download) |
| `--out` | No | Output CSV path |
| `--list-markets` | No | Print all available market names and exit |

## Execution

```bash
# List all available markets in the dataset
python tools/cot_fetch.py --list-markets

# S&P 500 and gold positioning — current year
python tools/cot_fetch.py --market "S&P 500" "GOLD" --year 2024

# Treasury futures
python tools/cot_fetch.py --market "10-YEAR" "2-YEAR" "30-YEAR" --year 2024

# FX majors
python tools/cot_fetch.py --market "EURO FX" "JAPANESE YEN" --year 2024

# Use cached ZIP to avoid re-downloading
python tools/cot_fetch.py --market "S&P 500" --zip .tmp/cot_raw_2024.zip
```

## Expected Output

A CSV with columns:

| Column | Description |
| --- | --- |
| `date` | Report date (weekly, typically Tuesday) |
| `market` | Full CFTC market name |
| `market_label` | Your query string (useful when pulling multiple markets) |
| `open_interest` | Total open interest |
| `nc_net` | Non-Commercial net (longs minus shorts) — large speculators |
| `comm_net` | Commercial net (longs minus shorts) — hedgers |
| `nr_net` | Non-reportable net — small traders |

## Key CFTC Market Name Fragments

| Query | Matches |
| --- | --- |
| `S&P 500` | S&P 500 FUTURES (CME) |
| `NASDAQ` | NASDAQ-100 FUTURES (CME) |
| `10-YEAR` | 10-YEAR T-NOTE FUTURES (CBOT) |
| `2-YEAR` | 2-YEAR T-NOTE FUTURES (CBOT) |
| `30-YEAR` | 30-YEAR T-BOND FUTURES (CBOT) |
| `EURO FX` | EURO FX FUTURES (CME) |
| `GOLD` | GOLD FUTURES (COMEX) |
| `CRUDE OIL` or `WTI` | CRUDE OIL FUTURES (NYMEX) |
| `VIX` | VIX FUTURES (CBOE) |

Use `--list-markets` to discover exact names if a query returns no results.

## Notes and Constraints

- **Release schedule**: CFTC publishes each Friday for positions as of the prior Tuesday. Data lags by 3 business days.
- **History**: The year-by-year ZIPs go back to 1986 for most financial markets. Use `--year` to pull prior years.
- **File size**: Each annual ZIP is ~2–4 MB. The tool caches the downloaded ZIP in `.tmp/` to avoid re-downloading on subsequent runs.
- **Legacy vs. Disaggregated**: This tool uses the "legacy" COT format (3 categories). The disaggregated format (Managed Money, Swap Dealers, etc.) provides more granularity but has shorter history. A separate tool handles disaggregated data.
- **Market name variations**: CFTC market names include the exchange suffix (e.g., "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE"). Use `--list-markets` to find the exact string if a query fails.

## Common Errors

| Error | Cause | Fix |
| --- | --- | --- |
| HTTP 404 on download | Year not yet published, or URL changed | Check cftc.gov/MarketReports/CommitmentsofTraders |
| `No market found matching` | Query doesn't match any market name | Run `--list-markets` and search manually |
| Empty DataFrame | Date parsing failed | Inspect raw CSV columns with `--list-markets` |

## Downstream Use

- Visualize net positioning: use `tools/chart_macro.py` with `--left nc_net comm_net`
- Overlay with price data: join on date with a price series from `fred_fetch.py` or yfinance
