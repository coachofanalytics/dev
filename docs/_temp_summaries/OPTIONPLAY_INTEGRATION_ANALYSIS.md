## OptionPlay legacy integration analysis (Opions_play_automation)

Source repo: [coachofanalytics/Opions_play_automation](https://github.com/coachofanalytics/Opions_play_automation)

### 1) What the legacy repo does
- Method: Headless browser scraping of OptionsPlay Hub pages via Playwright, then HTML table parsing with BeautifulSoup → pandas DataFrames → writes to PostgreSQL.
- Entry points (from `main.py`):
  - `main_cread_spread()` scrapes `https://www.optionsplay.com/hub/credit-spread-file`
  - `main_shortput()` scrapes `https://www.optionsplay.com/hub/short-puts`
  - `main_covered_calls()` scrapes `https://www.optionsplay.com/hub/covered-calls`
- Auth: Page login form fill using `USERNAME` and `KEY` environment variables.
- Parsing: `parse_data(html, choice)` selects table by id (e.g., `CreditSpreadFile_wrapper`, `coveredCalls_wrapper`, `shortPuts_wrapper`) and converts to DataFrame.
- Filtering/merging: `utils.merged_data()` merges unusual volume and liquidity CSVs and filters symbols (also enriches via yfinance EBITDA); `utils.process_data()` normalizes columns and adds metadata.
- Persistence: SQLAlchemy `.to_sql(...)` with `if_exists='replace'` into tables: `investing_credit_spread`, `investing_covered_calls`, `investing_shortput`.
- Config/env expected: `USER`, `PASSWORD`, `HOST`, `DATABASE` (DB creds), `USERNAME`, `KEY` (web login), optional `SOME_SECRET`.
- Dependencies: Playwright, BeautifulSoup, pandas, SQLAlchemy, psycopg2, yfinance (see `requirements.txt`).

### 2) Key differences vs current CODA implementation
- Data source:
  - Legacy: Scrapes web UI (fragile if DOM changes; requires headless browser; relies on site credentials).
  - Current CODA: Designed for official API integration (`PositionFetcherService` calls `https://api.optionplay.com/v1/...` when `OPTIONPLAY_API_KEY` is set), with Thinkorswim fallback and mock mode.
- Destination schema:
  - Legacy: Writes to standalone tables (`investing_credit_spread`, etc.).
  - Current CODA: Normalizes into `SuggestedPosition` model, driving staff review → batch → client approval.
- Scheduling:
  - Legacy: Intended via GitHub Actions (external runner).
  - Current CODA: Celery Beat/Heroku Scheduler first-class support.
- Business filters:
  - Legacy: CSV- and yfinance-driven filters (EBITDA > 0, price/volume thresholds) + merge with liquidity/unusual volume.
  - Current CODA: POP ≥70%, premium ≥$100, DTE 30–60, strategy allowlist; normalized greeks; AI fields.

### 3) Security and reliability considerations
- Headless scraping requires storing website username/password; higher risk than a scoped API key.
- DOM brittleness: Any OptionsPlay Hub page change breaks selectors.
- `.to_sql(..., if_exists='replace')` drops data each run; not idempotent for production pipelines.
- Direct DB access from an external runner can bypass Django validation.

### 4) What is reusable
- Normalization/column cleanup patterns (lowercasing, renaming, currency stripping).
- The concept of merging liquidity/unusual volume screens and valuation signals prior to selection.
- If API approval is delayed, the scraping flow can be used as a stopgap signal source.

### 5) Integration options

Option A — Inline reuse (recommended for speed and maintainability)
- Extract only the fetch+normalize logic into `coda/investing/services/optionplay_integration_service.py` as a source provider that returns normalized dicts matching our `SuggestedPosition` fields.
- Do NOT reuse direct DB writes; instead map into `SuggestedPosition` via `PositionFetcherService`.
- Keep scheduling in Celery Beat/Heroku Scheduler; use `OPTIONPLAY_API_KEY` when available, otherwise the stopgap provider may call the Hub scraper.
- Pros: Single codebase, minimal moving parts, aligned with our services layer and review workflow.
- Cons: You lose direct CSV/table dumps (which we don’t need).

Option B — External poster (decoupled)
- Keep legacy repo as a separate runner (GitHub Actions). It collects and normalizes, then POSTs results to a new CODA endpoint `/investing/api/suggestions/ingest` (token-protected), which persists to `SuggestedPosition`.
- Pros: Decoupled releases, easy to iterate outside main app.
- Cons: More moving parts (network, tokens, endpoint), additional maintenance.

Option C — Submodule/library
- Add the repo as a git submodule at `external/Opions_play_automation`, import its functions, and call from our service adapter.
- Pros: Avoid code copy; can update independently.
- Cons: Submodule complexity; API surface not designed as a library; scraping fragility remains.

### 6) Recommended path
1) Short term (this week): Option A without scraping. Use our existing mock flow for demos today; once `OPTIONPLAY_API_KEY` is approved, enable the official API path (already present in `PositionFetcherService`).
2) If approval delays persist and we need live-like data: implement a temporary adapter that invokes the legacy scraping fetcher behind a feature flag, mapping results to `SuggestedPosition`. Keep it internal (no external DB writes), and gate it to run only on dev/UAT.
3) Long term: Remove scraping; rely on the official OptionPlay API with Thinkorswim fallback. Retain liquidity/unusual-volume/yfinance enrichment in a safe, rate-limited service if desired.

### 7) Concrete mapping to CODA
- Source integration point: `coda/investing/services/position_fetcher_service.py` → `_fetch_from_optionplay()` and normalization helpers.
- Destination: `SuggestedPosition` model (probability_of_profit, premium_collected, dte, legs, greeks, etc.).
- Scheduling: `coda/investing/tasks.py` and `coda/celeryapp.py` (beat schedule already includes daily fetch).
- Config: `OPTIONPLAY_API_KEY` on Heroku; for temporary scraping fallback, store `OPTIONPLAY_USERNAME`/`OPTIONPLAY_PASSWORD` only in UAT if absolutely necessary.

### 8) Next steps
- If you choose Option A now: I will add a thin `optionplay_integration_service.py` with a provider interface, keep API-first logic, and prepare a toggle for a temporary scraper-backed provider (disabled by default).
- If you choose Option B: I will add `/investing/api/suggestions/ingest` and a token-based auth scheme, and provide a minimal JSON contract for the external runner.

References
- Repo under study: `https://github.com/coachofanalytics/Opions_play_automation`
- OptionsPlay API docs: `https://api.optionplay.com/docs`

