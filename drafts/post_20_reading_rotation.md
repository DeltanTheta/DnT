# Reading Rotation: How 60 Days of Flow Got Us Here

*DeltaTheta | Post 20 of the Build Series*

*Written by Claude with oversight.*

Post 19 introduced the flow lens: a snapshot of where capital is sitting right
now, ranked by conviction across three timeframes. That snapshot told you what
to overweight and underweight today. It didn't tell you how we got here.

This post zooms out. The same data that produces the ranked watchlist also
contains 869 trading days of CMF history. Running it as a time series shows you
which sectors have been building flow for weeks, which just reversed, and which
have been consistently leaking capital for a quarter. That context is what turns
a positioning call into a rotation read.

---

## The Rotation Cycle

Sector rotation describes the tendency for capital to move through sectors in a
predictable sequence tied to the economic cycle. The pattern — attributed to
the Merrill Lynch Investment Clock and popularized by strategists like Sam Stovall
— runs roughly as follows:

**Early recovery:** Consumer Discretionary and Technology lead. Risk appetite
returns, earnings expectations rise, cyclicals attract capital first.

**Mid-cycle expansion:** Industrials, Materials, and Energy outperform as the
physical economy catches up to financial conditions. Flow shifts from growth
into volume-driven sectors.

**Late cycle:** Energy and Materials continue, but Defensives — Consumer Staples,
Health Care, Utilities — begin to attract capital as the expansion matures and
investors hedge against a turn. Financial conditions tighten.

**Contraction:** Defensives hold while cyclicals and rate-sensitive sectors
(Real Estate, Discretionary) sell off. Fixed Income attracts inflows as yields
fall. Gold may rise depending on whether the contraction is inflationary or
deflationary.

The rotation doesn't always follow this sequence cleanly or on the same schedule.
But when you plot 30-day CMF over time across the three groups — cyclicals,
defensives, macro proxies — the relative flow direction tells you where capital
thinks we are in that sequence, without requiring anyone to call the cycle.

---

## The Tool

`flow_trend.py` reads the CSV produced by `capital_flows.py` and plots 30-day CMF
over the past 60 trading days for all 13 proxies, organized into three panels.

```
python tools/capital_flows.py
python tools/flow_trend.py
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

Saved 869 rows × 39 cols → E:\DnT\.tmp\capital_flows_20260622.csv

Flow Trend Chart  —  2026-06-22  (60-day lookback)
Chart saved -> E:\DnT\.tmp\flow_trend_20260622.png
```

---

## Reading the Three Panels

![Capital Flow Trends — 30-Day CMF, 60-Day Lookback](../.tmp/flow_trend_20260622.png)

### Cyclicals Panel

The most important line in the Cyclicals panel is Technology (purple). From early
April through mid-May, XLK ran from near-zero CMF to a peak of roughly +0.40 —
the strongest sustained inflow reading in the entire 13-ticker universe over this
window. That move reflects a clear structural accumulation phase: buyers were
consistently dominant on volume over a multi-week period. Since mid-May, the
30-day reading has been declining, but the descent has been gradual and XLK still
holds above zero as of the last trading day. The structural bid is intact; what
changed is the pace.

Energy (blue) tells a different story. It spiked sharply in late April, briefly
touching positive territory before reversing hard through May and into June, now
sitting modestly negative. That spike-and-fade pattern is characteristic of a
tactical rotation rather than a structural shift — capital rotated briefly into
Energy, probably on a commodity catalyst, but did not sustain. Industrials (green)
followed a similar arc with less amplitude: positive in April, fading through May,
now negative and carrying the divergence flag from the watchlist. The 30-day CMF
for XLI is declining even as price has held — the distribution setup Post 19
flagged is visible as a slow, grinding rollover on this chart.

Materials (orange) and Consumer Discretionary (red) have been the weakest
cyclicals throughout the window, spending most of the 60 days in negative or
near-zero territory. Materials had a brief positive excursion in mid-May but gave
it back sharply — now the weakest cyclical reading on the panel. The spread
between Technology (the strongest) and Materials (the weakest) represents the
quality bifurcation inside cyclicals: capital is not rotating into cyclicals
broadly, it is staying parked in the highest-multiple, most liquid end of the
complex.

### Defensives Panel

The Defensives panel shows the most dramatic reversals of the three panels.
Consumer Staples (blue) entered the window with the highest CMF reading in the
group — roughly +0.30 in early April — and has fallen continuously since, ending
as one of the most negative lines on the panel at around −0.19. That is a
complete reversal of a defensive bid over 60 trading days. When capital exits
Consumer Staples at this pace and magnitude, the interpretation is consistent
with a risk-on rotation: investors who had rotated into safe havens are unwinding
those positions and moving back toward growth assets.

Utilities (orange) traced a similar but less extreme arc. It was positive through
much of April and into May, peaked near +0.20, then sold off into negative
territory by June. Health Care (green) ran up briefly in May — the sharpest
single spike in the group — before reversing and declining toward negative. Real
Estate (red) has been the most consistently negative defensive throughout the
entire window, rarely breaking above zero and currently sitting near its worst
reading. Real Estate's persistent outflow reflects the rate sensitivity of the
sector: with the long end of the yield curve still elevated, capital continues to
leak from REITs regardless of the broader risk environment.

Communication Services (purple) has largely tracked the middle of the group —
not the worst defensive, but not recovering either. The overall picture across
the Defensives panel is one of sustained distribution following what may have
been a late-cycle defensive rotation in early April. The fact that all five
defensives are now negative or declining is the opposite of a late-cycle signal.
It suggests capital moved into defensives earlier in the window (possibly on a
risk-off macro event in April) and is now rotating back out.

### Macro Proxies Panel

The Macro Proxies panel is the most compressed in amplitude — all three lines
spend most of the 60-day window between −0.20 and +0.20 — but the relative
positioning contains useful information. Financials (blue/XLF) spent April near
flat, then built a steady positive CMF trend through May, peaking near +0.15
before pulling back modestly into June. The rise-and-partial-retreat in XLF is
consistent with a credit expansion environment that hit a soft patch: financials
attracted capital as rate expectations evolved, then gave back some of that gain
as macro uncertainty returned. The current XLF reading is near zero — neutral,
not bearish, which is consistent with the watchlist's HOLD/WATCH call.

Fixed Income (TLT, orange) was modestly negative in April — bond sellers were
in control during the period when equities were recovering. Through May, TLT
turned positive and has held a slight positive lean into June. The move is small
(peak near +0.10) but the direction matters: the bond market is slowly
reaccumulating, which means the yield curve is seeing quiet demand even as equity
flows remain constructive. This is not a flight-to-safety bid — the magnitude
is too small for that — but it may reflect positioning ahead of a potential rate
move.

Gold (green) is the most instructive line in this panel. In early April, GLD
showed a sharp positive spike — the clearest safe-haven bid in the dataset,
briefly reaching near +0.30. That spike has been entirely given back. Gold is
now among the most negative readings in the entire universe, sitting near −0.11
on the 30-day window with a sharply negative 5-day reading. The Gold reversal
is a regime signal: whatever risk-off event drove the April bid has resolved
from the market's perspective, and the safe-haven premium has been aggressively
unwound. The fact that TLT has gone slightly positive while Gold has gone sharply
negative suggests the bond bid is driven by rate expectations rather than
fear — a meaningfully different macro interpretation.

---

## Where We Are

The combined signal from all three panels describes a market that rotated
defensively in early April — Consumer Staples, Utilities, Gold all saw capital
inflows simultaneously — and has been unwinding that defensiveness ever since.
Technology absorbed the capital coming out of defensives and held its structural
bid through the full 60-day window, while the broader cyclical complex (Materials,
Industrials, Discretionary) did not meaningfully participate. That pattern is
consistent with a mid-expansion environment where growth expectations are intact
but the physical economy sectors have not yet confirmed. The key signal to watch
over the next 30 to 60 days is whether Industrials and Materials begin to recover
their CMF readings as Technology's 30-day reading fades — that would be the
classic mid-cycle handoff from growth leadership to broad cyclical participation.
If instead Technology's CMF breaks below zero while defensives fail to recover,
the rotation is more consistent with a late-cycle topping pattern than a
mid-cycle consolidation.

---

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

*← [Post 19: The Flow Lens](#) | [Post 21: Divergence Signals →](#)*

— *DeltaTheta*
