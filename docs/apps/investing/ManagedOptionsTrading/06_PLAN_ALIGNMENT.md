# Managed Options Trading – Plan Alignment (Nov 2025)

This note reconciles the trading strategy plan (`docs/_temp_summaries/TRADINGPLAN.md`) with our current implementation. It highlights what is shipped, what is partially covered, and what remains outstanding.

---

## 1. Capital Deployment & Strategy Mix

| Plan Item | Status | Implementation Notes |
| --- | --- | --- |
| Separate sleeves for large-cap (5–15% moves) and small-cap (30–40% jumps) | **Partially implemented** | Current system tracks positions by account but does not segment sleeves automatically. We can add strategy tags or custom fields to distinguish large vs. small cap plays. |
| Monthly ROI target 8–12% with $30k base capital | **In progress** | Managed income summary calculates monthly projected income and coverage vs. target. Need an ROI dashboard showing realized % and comparing to plan targets. |
| Risk per trade capped at 2–3% of capital | **Implemented** | Position size and exposure rules enforce max dollar and percentage limits when entering trades. |
| Weekly max drawdown 5% | **Not implemented** | Requires monitoring component to aggregate weekly P&L and trigger halt/alerts. |

---

## 2. Signal Sources & Tooling

| Plan Item | Status | Implementation Notes |
| --- | --- | --- |
| Use Unusual Whales flow + OptionsPlay for entry signals | **Implemented / Instrumented** | UW enrichment populates client dashboard and ranking engine; OptionsPlay ingestion exists in suggestion pipeline. New reporting cards show UW contribution (share of suggestions, win-rate, realized P&L). |
| Maintain watchlists for large/small cap candidates | **Not implemented** | Manual lists currently maintained outside the system. Consider adding curated watchlist model or integration with screener exports. |
| ATR-driven stop-loss and profit targets | **Not implemented** | Exit automation still manual. Opportunity to extend `OptionsMonitoringService` with ATR/backtest-driven recommendations and auto close triggers. |

---

## 3. Automation & Execution

| Plan Item | Status | Implementation Notes |
| --- | --- | --- |
| Automate trade execution via Python/Django | **In progress** | Auto-approval, Mark Entered workflow, and broker credential storage are live. Broker API execution (starting with Schwab) is the next milestone. |
| Automated risk management & alerts | **Implemented / In progress** | Auto approvals, Twilio alerts, and scenario explorer exist. Need weekly drawdown alerting and Slack/Teams bridge for desk visibility. |
| Performance tracking dashboard | **Partially implemented** | Managed account detail shows scenario projections, income history, and open positions. Still need aggregated win-rate (machine vs. human) and strategy-level performance views. |

---

## 4. Next Recommended Enhancements

1. **Broker Execution Layer** – Build Schwab API client and order mapping so approved positions can be placed automatically.  
2. **Strategy Segmentation** – Tag positions as large-cap vs. small-cap sleeves and surface allocation stats on dashboards.  
3. **Drawdown Guardrails** – Implement weekly drawdown report + auto-pause logic when the 5% threshold is crossed.  
4. **Signal Attribution Metrics** – Instrument wins/losses by source (UW, OptionsPlay, manual) to justify data subscriptions.  
5. **Stop/Exit Automation** – Extend monitoring service with ATR-based exit triggers and optional auto-close.  
6. **Operator UI for automation knobs** – Provide staff console controls for parameters like `AUTO_APPROVE_TOP_N`, risk tolerances, and broker toggles.

These items bring us fully in line with the trading plan and support the “world-class” automation vision.

