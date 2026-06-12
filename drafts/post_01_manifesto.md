# Building a Hedge Fund Research Desk for One

*DeltaTheta | Post 1 of the Build Series*

*Written by Claude with oversight.*

There are two kinds of macro research.

The first kind is what you can access as an independent trader: scattered data portals, fragmented free tools, newsletters that tell you what happened but never how they arrived at the conclusion, and a parade of upsells promising to reveal the part they held back. The framework — the actual process for connecting CPI to yields to positioning to price — is always the thing that isn't included.

The second kind is what an institutional shop runs: a systematic data pipeline that ingests dozens of sources on a schedule, a structured research process that forces analysts to document their theses and assumptions, and a quantitative layer that translates macro views into measurable signals. Bloomberg terminals. Prime brokerage data. A team of analysts.

I've been trading macro as an independent for years. The cost gap is real — Bloomberg alone is $24,000 a year before you pay for anything else. But the more I sat with it, the more I realized the cost isn't actually the main problem. The main problem is that even when the data is free — and most of the core macro data is free, published by government agencies and the Federal Reserve — there's no publicly documented framework for how a serious practitioner uses it. The process is the proprietary part. The connective tissue is what gets sold.

AI changes that equation in a specific way. Not because it can read charts or predict markets — it can't, and anyone claiming otherwise is selling something. It changes it because it can be a genuine thinking partner for designing and maintaining a research process. It can help architect a system, write the code to automate data collection, draft the analytical frameworks, and flag when the logic breaks down. It turns a solo practitioner into something that functions like a small research team.

That's what DeltaTheta is documenting.

---

## What We're Building

This is a build-in-public journal. Every post will show actual work: the tools we write, the workflows we define, the Claude conversations that shaped the design decisions, and the failures we hit along the way. Nothing is sanitized after the fact.

The system we're building has three layers — I'm calling it the WAT framework (Workflows, Agents, Tools)¹:

**Layer 1 — Workflows**: Plain-language standard operating procedures that define the objective, the inputs, the steps, and how to handle errors. Written like you'd brief a smart colleague.

**Layer 2 — Agents**: This is where Claude operates. The agent reads the relevant workflow, decides which tools to run and in what order, handles failures, and asks clarifying questions when the instructions run out. The agent is responsible for reasoning; the tools are responsible for execution.

**Layer 3 — Tools**: Python scripts that do the actual mechanical work — API calls, data cleaning, chart generation, file operations. Deterministic. Testable. Fast.

Why separate them? Because when AI tries to handle every step directly, errors compound. If each step is 90% accurate, you're at 59% success after five steps. By offloading execution to code that always does exactly what it's told, the agent can stay focused on the reasoning where it actually adds value.

---

## What We're Not Doing

No trade signals yet. No predictions. No "here's what the market will do next week."

That will come later, once we've built the data layer and the research framework on solid ground. Starting with signals is how you end up with a system optimized for backtesting nostalgia rather than live macro thinking.

We're also not going to pretend this is finished or polished. The project directory at `e:\DnT` is sparse by design — we build only what we need, when we need it:

```
e:\DnT\
├── CLAUDE.md          ← the WAT framework instructions
├── .env               ← API keys
├── tools\             ← Python scripts
├── workflows\         ← Markdown SOPs
└── .tmp\              ← intermediate files, disposable
```

That's the starting line. Everything else gets built in front of you.

---

## The Data Sources

All public. All free (with a free API registration where required):

- **FRED** (St. Louis Federal Reserve) — the backbone. Treasury yields, CPI, GDP, unemployment, M2 money supply, credit spreads. Every series the Fed publishes.
- **CFTC Commitments of Traders** — weekly positioning data for futures markets. Commercial vs. Non-Commercial. No API key needed — bulk CSV downloads directly from cftc.gov.
- **BLS** (Bureau of Labor Statistics) — employment and inflation direct from the source
- **BEA** (Bureau of Economic Analysis) — GDP, personal consumption, trade data
- Market prices — via free APIs for indices, FX, commodities

The data was never the expensive part. The framework is.

---

## What DeltaTheta Will Cover

The build will run in four series:

**Series 1 — The Foundation**: WAT framework, data ingestion, FRED pipeline. Boring infrastructure that makes everything else possible. (You're reading it now.)

**Series 2 — The Instruments**: Yield curves, COT reports, credit spreads, volatility regime. What each indicator measures, why it belongs in a macro framework, and the code to pull and display it.

**Series 3 — The Research Layer**: Structuring a macro thesis. What a hedge fund research memo actually contains. How to use an AI agent to stress-test your assumptions rather than confirm them.

**Series 4 — The Signal Layer**: Quantitative indicators. Systematic frameworks for translating macro views into measurable signals. This is the part where the work becomes tradeable — eventually.

---

## A Note on Transparency

Every conversation I have with Claude that shapes a design decision will be included. Every workflow file will be shown verbatim. Every error message and its fix will be documented.

This matters because the gap in independent macro research isn't the data — it's the process. That process is what I'm trying to make visible. If you can see exactly how this system gets built, decision by decision, you can build your own version, critique mine, or take the pieces that fit your approach and leave the rest.

That's what the second kind of research would look like if someone just showed their work.

---

Next post: **WAT — How We're Organizing the Machine**. I'll explain the framework architecture in detail and show the `CLAUDE.md` file that instructs the agent how to operate.

If you want to follow the build as it happens, subscribe. No upsell at the end. Just the work.

— *DeltaTheta*

---

*¹ The WAT framework architecture was developed by Nate at the [AI Automation Society](https://www.skool.com/ai-automation-society). We're applying it here to macro research with modifications documented as we go.*
