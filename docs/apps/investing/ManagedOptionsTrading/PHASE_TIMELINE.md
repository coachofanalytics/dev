# Managed Options Automation – Phase Timeline (2025)

> Snapshot compiled November 11, 2025 to capture the journey from manual approval pain points to the current UAT-ready automation stack.

## Phase 0 – Immediate Issues (Oct 2025)
- Client approval flow stalled; “Approve” button timing out and no error telemetry.
- Client expectation: auto-approve after 3 hours with a clear “awaiting trader entry” state.
- OptionPlay CSV uploads were manual; Unusual Whales (UW) data curated by hand once per batch.
- Pricing stack fragmented (legacy $420 plan + inactive tiers).

## Phase 1 – Trader Workflow Stabilisation
- Added `auto_approve_at/auto_approved_at` to `PositionBatch` and `OptionsPosition`.
- New “Mark Entered” action for traders; execution timestamps stored.
- Batch cron: auto-approve after 3 hours, expire at 24 hours; notifications wired to email + WhatsApp/SMS.
- Staff suggestions filter defaults to `EXCELLENT`; toggle exposes lower grades.
- Auto metrics surfaced (total, win-rate, avg realised P&L, entry lag).

## Phase 2 – Data Feed Hardening
- OptionPlay scraping formalised (`fetch_positions` management command) with Playwright fallback.
- Heroku slug now bundles Playwright browsers & system deps (via buildpack); UAT fetch button returns live spreads.
- UW integration enhanced: enrichment service attaches flow score & timing signal; prune job clears stale suggestions after configurable TTL.
- `SuggestedPositionOutcome` + `OptionPlayOutcomeService` evaluate expired ideas.
- Management commands:
  - `evaluate_optionplay_outcomes`
  - `rescore_suggested_positions`

## Phase 3 – Pricing & Onboarding Narrative
- ManagedTradingAccount choices rewritten:
  - `balanced` ($249/mo + 12% over 6% hurdle)
  - `consultative` legacy $420 plan (grandfathered)
  - `elite` preview (greyed out / coming soon)
- Onboarding form filters tiers by recommended risk presets; preview tiers rendered disabled.
- Fee calculations updated (`ManagedTradingService`) with tier defaults and hurdle logic.
- Docs refreshed (7-doc set + `PRICING_TIERS_2025.md`) to align messaging.

## Phase 4 – Notifications & Runbooks
- WhatsApp templates: `batch_auto_approved`, `auto_suggestions`.
- Twilio SMS/WhatsApp sending implemented with phone roster (`TRADER_ALERT_PHONES`).
- Runbooks created for Twilio smoke tests and Schwab onboarding credentials.

## Phase 5 – Demo Data & Analytics
- Seed scripts populate demo accounts, historical closed trades, and open positions for dashboards.
- Predictive analytics patched for NumPy 2.x (`np.float_` shim).
- Staff dashboard now includes UW snapshot, auto metrics, and “Show all ratings” button.
- Predictive page shows data once ≥3 closed trades exist; fallback forecast anchored to latest history.

## Phase 6 – Admin & UX Polish (Nov 11)
- `OptionsPositionForm` now editable for `current_value`, `unrealized_pnl`, `realized_pnl`; admin boolean field fixed.
- Staff suggestions banner shows last fetch timestamp using `django.contrib.humanize`.
- UAT slug (codamakutano) deployed with Playwright buildpack; fetch logs confirm live ideas (AMD, BKNG, ALC, NFLX).

## Outstanding for Production
- Production app (codatrainingapp) needs Playwright system deps (`playwright install-deps` or apt buildpack) before scraping works.
- Phase roadmap:
  1. Trader workflow polish (risk presets, Mark Entered audit trail).
  2. Portfolio/plan strategy (UW-only pipeline, rotation cadence, capital diversity).
  3. Pricing narrative & client dashboard widgets (read-only metrics, scenario explorer copy).
  4. Production rollout once Playwright + UW cadence locked and compliance copy approved.

## Quick References
- Staff suggestions: `/investing/managed/staff/suggestions/`
- Fetch command: `python manage.py fetch_positions --source optionplay`
- Rescore command: `python manage.py rescore_suggested_positions`
- Outcome evaluator: `python manage.py evaluate_optionplay_outcomes`
- Docs anchor: `docs/apps/investing/ManagedOptionsTrading/` (7-doc set, pricing guides, this timeline)

---

**Next updates**: fold future phases into this timeline as we complete trader preset enforcement, build client dashboards, and cut the production deployment.*** End Patch




