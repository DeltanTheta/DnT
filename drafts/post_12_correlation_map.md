# The Correlation Map: How Macro Assets Are Moving Together Right Now

*DeltaTheta | Post 12 of the Build Series*

*Written by Claude with oversight.*

Most market analysis treats assets in isolation — the stock went up, the bond went down, gold is rising. But the more useful question is structural: are these assets moving *together* or *apart*, and has that relationship changed recently? Correlation structure is the scaffolding that underlies portfolio behavior, risk parity fund mechanics, and macro regime identification. When the scaffolding shifts, it often signals something meaningful about the macro environment before it shows up in price levels.

This post introduces the correlation matrix tool built into this pipeline, walks through the current 63-day snapshot, and highlights the week-over-week shifts that are most worth tracking.

---

## The Proxy Map

Seven tickers, each standing in for a macro factor:

| Ticker | Asset | Macro Factor |
|--------|-------|-------------|
| SPY | S&P 500 ETF | Broad U.S. equity / risk appetite |
| IWM | Russell 2000 ETF | Small-cap / domestic growth sensitivity |
| QQQ | Nasdaq 100 ETF | Tech-weight equity / growth factor |
| TLT | 20+ Year Treasury ETF | Long duration / rate sensitivity |
| IEF | 7–10 Year Treasury ETF | Intermediate duration / rate benchmark |
| GLD | Gold ETF | Real asset / inflation hedge / risk-off store |
| DX-Y.NYB | U.S. Dollar Index | Dollar strength / global liquidity proxy |

These aren't exhaustive — they don't cover credit, commodities, or EM — but they cover the core macro axis that most professional portfolios are built around. Correlation across these seven gives a working map of the current regime.

---

## The Tool

The `correlation_matrix.py` script pulls 275 trading days of daily price history (roughly 13 months), computes log returns, and then calculates Pearson correlations over two overlapping 63-day windows: the current window and a window ending one week prior. The third panel shows the delta — what moved.

```bash
python tools/correlation_matrix.py
```

```
Fetching prices: SPY, IWM, QQQ, TLT, IEF, GLD, DX-Y.NYB
  Date range: 2025-05-13 to 2026-06-17

  OK  SPY           275 trading days  [2025-05-13 to 2026-06-16]
  OK  IWM           275 trading days  [2025-05-13 to 2026-06-16]
  OK  QQQ           275 trading days  [2025-05-13 to 2026-06-16]
  OK  TLT           275 trading days  [2025-05-13 to 2026-06-16]
  OK  IEF           275 trading days  [2025-05-13 to 2026-06-16]
  OK  GLD           275 trading days  [2025-05-13 to 2026-06-16]
  OK  DX-Y.NYB      276 trading days  [2025-05-13 to 2026-06-16]

Top 5 movers (prior → current):
  QQQ / DX-Y.NYB        -0.61 → -0.55  (+0.06)
  TLT / DX-Y.NYB        -0.49 → -0.43  (+0.06)
  SPY / DX-Y.NYB        -0.68 → -0.62  (+0.05)
  IEF / DX-Y.NYB        -0.57 → -0.53  (+0.04)
  SPY / GLD             +0.63 → +0.67  (+0.04)

Chart saved -> E:\DnT\.tmp\correlation_matrix_20260617.png
```

The window covers 63 trading days — approximately one quarter. The prior window ends five trading days earlier, so the delta panel captures what the most recent week added and removed from the structure.

---

## The Current Snapshot

![Correlation Matrix — June 17, 2026](.tmp/correlation_matrix_20260617.png)

### Panel 1: What the Current Structure Looks Like

**The equities cluster is tightly coupled.** SPY, IWM, and QQQ are moving nearly in lockstep over this window: SPY/IWM at +0.89, SPY/QQQ at +0.94, IWM/QQQ at +0.83. That level of internal coherence across large-cap, small-cap, and Nasdaq means equity-specific factor dispersion has been low — the market has largely been trading as a single risk-on/risk-off block rather than rotating between growth and value.

**Equities and duration are positively correlated — an unusual regime.** SPY/TLT is +0.52, SPY/IEF is +0.63, IWM/TLT is +0.62, IWM/IEF is +0.69, QQQ/TLT is +0.45, QQQ/IEF is +0.56. In the standard textbook model, rising rates (falling bonds) go with strong equities, so TLT and SPY should be negatively correlated. A prolonged positive correlation between equities and duration suggests the dominant driver over this window has been something that lifts both — typically rate *cut* expectations or a broad risk-on move responding to falling macro uncertainty. Both bonds and stocks rising together is a "good news for risk assets" correlation regime, as opposed to the "inflation shock" regime where they sell off together.

**The duration pair is extremely tight.** TLT/IEF at +0.93. This is expected — both track U.S. Treasuries — but it confirms these two are acting as near-perfect substitutes in the current window. No significant divergence between the long end and the intermediate end.

**Gold is correlated with equities.** SPY/GLD is +0.47, IWM/GLD is +0.58, QQQ/GLD is +0.64. Gold also has a meaningful positive relationship with duration: TLT/GLD is +0.41, IEF/GLD is +0.62. This is the profile of gold acting as a "dollar alternative" or "real asset long" rather than purely a defensive hedge. In a pure risk-off flight, gold tends to diverge from equities and move with bonds. Here, gold is moving broadly with the complex — suggesting the common driver may be dollar weakness or declining real rates rather than fear.

**The dollar (DXY) is negatively correlated with everything.** SPY/DXY is −0.62, IWM/DXY is −0.67, QQQ/DXY is −0.55, TLT/DXY is −0.43, IEF/DXY is −0.53, GLD/DXY is −0.37. A uniformly negative DXY relationship across equities, bonds, and gold is the hallmark of a "weaker dollar lifts all boats" regime. Dollar weakness acts as a liquidity expansion signal globally, loosening financial conditions without a Fed rate cut needing to actually happen.

### Panel 3: What Shifted This Week

The top five movers this week were all DXY-related, plus one GLD pair:

| Pair | Prior | Current | Change |
|------|-------|---------|--------|
| QQQ / DXY | −0.61 | −0.55 | +0.06 |
| TLT / DXY | −0.49 | −0.43 | +0.06 |
| SPY / DXY | −0.68 | −0.62 | +0.05 |
| IEF / DXY | −0.57 | −0.53 | +0.04 |
| SPY / GLD | +0.63 | +0.67 | +0.04 |

All five DXY correlations moved in the same direction: *less negative*. The inverse dollar relationship with equities and bonds weakened slightly across the board. This could reflect a brief period of dollar stabilization or recovery entering the new window, which diluted the prior week's contribution to the overall correlation. The SPY/GLD relationship ticked upward — gold and equities became slightly more tightly coupled, consistent with gold continuing to trade as a risk-asset correlate rather than a hedge.

None of these are large shifts. The overall regime — tight equity cluster, positive equity-duration relationship, broadly negative DXY — remains intact. The delta panel is flagging incremental moderation, not a regime break.

---

## Bottom Line

The current 63-day correlation structure reflects a broadly coordinated risk environment: equities move together, bonds move with equities, gold moves with equities, and everything has an inverse relationship with the dollar. That's the "dollar weakness as liquidity tailwind" regime. The week-over-week shifts are small and concentrated in the DXY pairs — the negative dollar correlations are softening slightly, suggesting some marginal dollar stabilization has entered the recent window. There is no sign of regime break in the data: the structure is intact, and the main open question is whether the equity-duration positive correlation persists or reverts toward the more typical inverse relationship as the macro picture evolves.

---

<a href="https://www.buymeacoffee.com/DeltanTheta" target="_blank">
<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png"
     alt="Buy Me A Coffee"
     style="height: 60px !important; width: 217px !important;" />
</a>
