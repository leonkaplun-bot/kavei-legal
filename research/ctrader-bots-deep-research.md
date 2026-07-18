# Deep Research: Free cTrader Bots (cBots) for Daytrading / Scalping

**Date:** 2026-07-18 · **Method:** multi-agent research workflow (101 agents, 5 search angles, 19 sources fetched, 25 claims adversarially verified by 3-vote panels — 24 confirmed, 1 refuted)

---

## The honest headline finding (verified unanimously)

**No free cTrader cBot — and no free/open-source MetaTrader EA — was found anywhere with credible evidence of long-term profitability.** Not one had a verified live track record (Myfxbook / FX Blue), a long realistic-cost backtest attached to the downloadable bot, or a sustained community reputation for actually making money. Every "Top 10 free profitable cBots" style page checked (ClickAlgo's roundup, ctrader.com product lists, EarnForex, MQL5 "best" lists) was rated **unreliable** by source extractors: marketing claims with zero verification.

This matches the economic reality: a genuinely profitable scalping system is almost never given away free. **Any free bot marketed as a "proven winner" should be treated as a marketing claim until backed by an independently verified live record. No bot guarantees profits.**

So the top-5 below is ranked by what CAN be honestly ranked: **code legitimacy, license, code quality, activity, and ease of use/porting to cTrader** — explicitly *not* by evidenced profitability, because nothing cleared that bar.

---

## Ranked Top 5 — best free, legitimately licensed bot code you can download today

### 1. Spotware `ctrader-algo-samples` — the official cTrader vendor repo
- **Download:** https://github.com/spotware/ctrader-algo-samples (also linked from the official docs: https://help.ctrader.com/ctrader-algo/documentation/cbots/cbot-code-samples/)
- **License:** MIT (free to use, modify, redistribute)
- **What it is:** Official cBot / indicator / plugin samples for the cTrader Automate API, 100% C#, actively maintained (updated July 2026, 337 commits).
- **Why #1:** The canonical, safest starting point — vendor-maintained, no malware/licensing risk, and the reference codebase for porting any MetaTrader EA to cAlgo.
- **Risks:** These are educational API demos, not tuned strategies. No performance claims at all (which is a point in their favor for honesty).

### 2. `geraked/metatrader5` — 13 open-source MT5 EAs, best porting candidates
- **Download:** https://github.com/geraked/metatrader5 (570 stars, active through Nov 2025)
- **License:** MIT — legally free to port to cTrader's C# cAlgo API
- **What it is:** 13 indicator-based EAs (Chandelier Exit + ZLSMA, Bollinger Bands + RSI, dual MACD + Stochastic, Nadaraya-Watson Envelope + RSI + ATR, Linear Regression Candles + UT Bot, etc.), each with an author-supplied backtest report and the source strategy video linked.
- **Why #2:** The only candidate found with *any* per-strategy performance documentation, clean readable MQL5 that maps well to C#.
- **Risks:** Evidence is **author-supplied backtests only** — no live verified record; vulnerable to over-optimization. **The author himself warns** that some EAs add a grid (averaging-down) layer "to forcefully enhance profitability... but this approach also introduces significant risk" — textbook grid-blowup risk. Prefer the non-grid variants and re-backtest with realistic spread + commission before any live use.

### 3. ClickAlgo `ctrader` sample repo — ~120 ready-made cBot projects
- **Download:** https://github.com/ClickAlgo/ctrader
- **License:** MIT
- **What it is:** ~120 robot sample folders (grid samples, RSI reversal, trade-management bots, etc.) from the biggest third-party cTrader vendor, current as of 2025.
- **Why #3:** The largest collection of directly-runnable cTrader cBot source. Good for learning patterns and assembling your own daytrade logic.
- **Risks:** Every bot is explicitly disclaimed as educational ("does not guarantee any particular outcome or profit of any kind"); no performance evidence; the repo is partly a funnel to ClickAlgo's paid products. Their marketing pages ("10 Best Free cTrader Bots") were rated unreliable — use the code, ignore the ranking claims.

### 4. `EA31337` / `EA31337-Libre` — 35+ strategy framework (study/porting only)
- **Download:** https://github.com/EA31337/EA31337 and https://github.com/EA31337/EA31337-Libre (237 stars)
- **License:** GPLv3 — free, but any distributed cTrader port must also stay open-source
- **What it is:** The highest-profile open-source multi-strategy Forex robot for MT4/MT5 (35+ strategies), a zero-cost library of strategy logic to mine and port.
- **Why #4:** Breadth of strategy implementations you can study and selectively port.
- **Risks:** **Its own docs say it is not recommended for real trading** and carry the CFTC "simulated results do not represent actual trading" disclaimer. Last release Aug 2023; large C++/MQL codebase = substantial porting effort. Strictly a study resource.

### 5. `srlcarlg/srl-ctrader-indicators` — free order-flow scalping toolkit for cTrader
- **Download:** https://github.com/srlcarlg/srl-ctrader-indicators (73 stars, updated July 2026)
- **License:** Apache-2.0
- **What it is:** Not a bot — an order-flow suite native to cTrader: Order Flow Ticks, Volume/TPO Profile, Weis & Wyckoff tools, Anchored VWAP, Renko. These are the inputs serious scalpers actually use.
- **Why #5:** For scalping/daytrading, high-quality free order-flow tooling on cTrader is rarer and more valuable than another unverified "scalper EA." Feed these into your own cBot logic.
- **Risks:** No track record (it's tooling); the author now focuses on paid cTrader Store versions, but the Apache-2.0 repo remains free.

---

## Explicitly avoid

- **`GeneralD/calgo`** (claims 200+ indicators, 75+ cBots): archived, zero traction, targets the obsolete .NET Framework 4.x cTrader, and — decisively — **has no license** while admitting it mixes in code collected from cTDN/MQL4 sources. Legally unclear to reuse; the claim that it's a usable open-source cBot source was *refuted* in verification (1–2 vote).
- Any free bot whose "proof" is a vendor screenshot, a demo-account curve, or a backtest without spread/commission/slippage settings shown. Common scam patterns: curve-fit backtests, zero-slippage demo accounts, martingale equity curves that look smooth until the account blows up.

## Porting MT4/MT5 → cTrader: practical notes

- Almost nothing is drop-in: of the 62 repos in GitHub's `expert-advisors` topic, only 6 are C# — everything else needs an MQL→C# rewrite against the cAlgo API (use the Spotware samples in #1 as the reference).
- The **2calgo** MQ4→cAlgo converter's website is dead (403/connection reset), but its source remains on GitHub.
- License rules: MIT code (geraked, Spotware, ClickAlgo) → port freely, keep the notice. GPLv3 (EA31337) → distributed ports must stay open-source. Unlicensed (GeneralD/calgo) → don't reuse.
- Also worth browsing: the MQL5 CodeBase free-EA section (source included) — but its ratings measure downloads, not profitability.

## Scalping-specific caveats (apply to ALL of the above)

1. **Broker execution decides everything.** A scalper that backtests profitably dies on 0.3 pips of extra spread, commission, or slippage. Only consider raw-spread + commission accounts, re-backtest with tick data and realistic costs, and forward-test on demo for months first.
2. **Grid/martingale = tail blowup risk.** Smooth equity curves from averaging-down strategies hide a single catastrophic loss. The geraked author flags this himself.
3. **Prop firms and brokers restrict bots.** Most prop firms ban or restrict grid/martingale, HFT/latency scalping, and sometimes any third-party EA; some brokers penalize scalping. Check the rules before deploying anything.
4. **GitHub stars ≠ profits**, and star counts can be gamed (one repo in the index showed signs of star inflation).
5. **Past (simulated) performance does not indicate future results. No bot, free or paid, guarantees profits.**

## Open questions (not fully crawled in this pass)

- The cTrader Store free section, ClickAlgo's website free downloads, cTDN forum archives, and Forex Factory / ForexPeaceArmy threads were not deep-crawled — a free bot with a genuine verified record *could* exist there, though the pattern makes it unlikely.
- Whether geraked's non-grid strategies survive an out-of-sample re-backtest with realistic costs when ported to cAlgo.
- Current 2026 automation rules of major prop firms (FTMO etc.) per strategy type.
