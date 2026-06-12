# WAT — How We're Organizing the Machine

*DeltaTheta | Post 2 of the Build Series*

*Written by Claude with oversight.*

Last post ended with a promise: show the framework in detail and publish the actual file that instructs the agent how to operate. That's this post.

Before we get into it — a note on attribution. The WAT framework (Workflows, Agents, Tools) was developed by Nate at the [AI Automation Society](https://www.skool.com/ai-automation-society), a Skool community focused on building practical AI automation systems. This series draws heavily on those materials and that architecture. We're applying WAT to macro research specifically, with modifications we'll document as they emerge. If you want to go deeper into the framework itself — the theory, the general patterns, the broader applications — the AIS community is where that conversation lives. What we're doing here is narrow: one domain, shown in full detail.

Now, to the machine.

---

## Why the Architecture Matters Before Anything Else

It's tempting to skip the scaffolding and start pulling data. I've done it. You end up with a folder of scripts that work individually and compose poorly, a set of conventions that made sense at the time and are now embedded too deep to change, and a growing debt of implicit knowledge that lives only in your head.

The WAT framework exists to prevent that. Its central claim is that AI-augmented systems fail — reliably and in a specific way — when the AI is asked to do too much. Not because the model is weak, but because the architecture is wrong.

Here's the failure mode: if each step in a chain is 90% accurate, five steps gets you to 59% overall success. That's not a model problem. That's a composition problem. The answer isn't a better model — it's fewer steps in the AI's hands.

WAT solves this by separating three things that most people run together.

---

## Layer 1 — Workflows: The Instructions

A Workflow is a plain-language standard operating procedure stored as a Markdown file in `workflows/`. It defines:

- **Objective** — what we're trying to accomplish
- **Inputs** — what needs to exist before we start
- **Steps** — which tools to call, in what order, with what parameters
- **Expected outputs** — what success looks like
- **Edge cases** — what to do when things go wrong

The critical constraint: a Workflow doesn't contain code. It's not a script. It's the kind of document you'd write to brief a smart colleague who hasn't seen this task before. It can be read by a human, edited by a human, and understood without a programming background.

Here's a slice of the FRED data workflow at `workflows/fred_data.md` to make this concrete:

```
## Execution
Run the following command to fetch data:

    python tools/fred_fetch.py --series DGS2 DGS10 T10Y2Y --start 2000-01-01 --out .tmp/

## Known Constraints
- Rate limit: 120 requests per minute. Space requests if pulling many series.
- Some series have varying release frequencies (monthly vs daily). Don't 
  compare raw values across mismatched frequencies without resampling first.
- Data reflects vintage at time of pull. FRED revises historical data. 
  Note the pull date in your analysis.
```

No implementation. No Python. Just instructions — clear enough to execute from, flexible enough to evolve.

Workflows are living documents. When we hit a constraint we didn't anticipate, when a tool changes behavior, when we find a better approach — the workflow gets updated. The goal is that anyone picking up this project a year from now can read the workflows directory and understand exactly how to operate the system.

---

## Layer 2 — Agents: The Decision-Maker

The Agent is where Claude operates. Its job is coordination, not execution.

When a task arrives — "pull the latest yield curve data and build a chart" — the agent reads the relevant workflow, identifies the required inputs, decides which tools to call and in what order, handles errors if they appear, and asks for clarification when the instructions run out. It does not attempt to fetch data directly. It does not write code on the fly and run it in its own context. It reads instructions and calls tools.

This distinction matters more than it sounds. An AI model reading raw external data is an injection surface — the data source can contain content that manipulates the model's behavior in ways that are invisible to you. A Python script reading the same data parses it mechanically and hands you back structured output. Nothing in the data can tell the script what to do differently.

There's also a cost argument. Running a reasoning step through a language model costs tokens every time. Running the same logic in a Python script costs essentially nothing per execution. As the pipeline scales, that difference compounds.

The agent's instructions live in a file called `CLAUDE.md` at the root of the project directory. Claude reads this file at the start of every session. The current version is published verbatim in the GitHub repo: [CLAUDE.md on GitHub](https://github.com/DeltanTheta/DnT/blob/main/CLAUDE.md).

A few things worth noting about that file.

The tone is deliberate. It's written the way you'd brief a contractor who is competent but new to the project — direct, specific about what matters, explicit about what the work is not. Vague instructions produce vague outputs.

The "Primary Output" section is new as of this post. After running the pipeline through the first data pulls, it became clear that the agent's natural instinct is to try to do things directly — fetch a URL, read a file, reason through a data structure inline. Those instincts are expensive and, for external data, potentially exploitable. So we made it explicit: when in doubt, write a script.

The self-improvement loop at the bottom is not rhetorical. Every time a tool breaks and gets fixed, the fix goes into the code and the lesson goes into the workflow. The system is supposed to get more robust with use, not just more complicated.

---

## Layer 3 — Tools: The Execution

Tools are Python scripts in `tools/`. They are:

- **Deterministic** — the same inputs always produce the same outputs
- **Testable** — you can run them in isolation and verify they work
- **Scoped** — each script does one thing and does it completely
- **Documented** — the corresponding workflow explains when and how to use it

Currently in the pipeline:

```
tools/
├── fred_fetch.py      ← pull any FRED time series by ID to CSV
├── chart_macro.py     ← generate publication-quality macro charts
└── make_header.py     ← generate Substack header images
```

`fred_fetch.py` is the workhorse. It accepts a list of FRED series IDs, a date range, and an output directory. It handles authentication, rate limiting, and outputs clean CSVs. The agent never touches FRED directly — it calls this script.

`chart_macro.py` handles visualization. It generates dual-axis charts with recession shading, a consistent color palette, and formatting appropriate for publication. The Post 1 yield curve chart was produced by this tool.

`make_header.py` generates the 1200×630 OG image that appears when you share a Substack post. It pulls from the same yield curve data and applies the DeltaTheta branding.

Every tool we add going forward will follow the same pattern: scoped, documented in a corresponding workflow, callable by the agent without modification.

---

## What the Directory Looks Like Now

```
DnT/
├── CLAUDE.md                    ← agent instructions
├── .env                         ← API keys (gitignored, never committed)
├── tools/
│   ├── fred_fetch.py
│   ├── chart_macro.py
│   └── make_header.py
├── workflows/
│   └── fred_data.md
└── .tmp/                        ← generated files, disposable, gitignored
    ├── fred_DGS2_DGS10_T10Y2Y_20260611.csv
    ├── yield_curve_2000_2026.png
    └── header_post01.png
```

Sparse by design. Nothing exists in this directory unless it's been built in front of you.

---

## A Note on Going Deeper

We're adapting WAT for a specific domain, and this post covers what's relevant for that application. But the framework is broader and more developed than what you're seeing here. Nate and the [AI Automation Society community on Skool](https://www.skool.com/ai-automation-society) have done the foundational work — the pattern library, the agent design principles, the broader case studies. If you're interested in WAT as a general architecture for building AI-augmented systems — not just macro research pipelines — that's the right place to go. This series will continue assuming you're here for the macro application specifically.

---

Next post: **The Yield Curve — What It Measures, Why It Belongs, and the Code to Pull It**. We'll walk through `fred_fetch.py` in detail, explain the economic logic behind the 2s10s spread and its variants, and produce the first real analytical output from the pipeline.

If you want to follow the build, subscribe. Still no upsell. Still just the work.

— *DeltaTheta*

---

*¹ The WAT framework architecture was developed by Nate at the [AI Automation Society](https://www.skool.com/ai-automation-society). This series draws directly on those materials and applies them to macro research. The AIS community is the right starting point if you want to understand the framework beyond this narrow application.*
