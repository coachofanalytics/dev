# Employee Activity System (Management) – 02_REQUIREMENTS.md

## Functional Requirements (What)
1. DRY Foundation (Phase‑0 – DONE)
   - Consolidate utilities, base views/models and shared templates.
   - Provide smoke tests covering consolidated components.
2. Data Pipeline (Phase‑1)
   - Ingest TaskHistory and meeting metadata (from ai_services: GoToMeeting).
   - Normalize Department → Category → Task relationships.
   - Expose query/report endpoints for historical analysis.
3. Evidence Automation (Phase‑1)
   - Auto‑link meetings to tasks based on time, participants, title/keywords.
   - Manual review/override UI for mismatches.
4. AI‑Assisted Assignment (Phase‑1/2)
   - Heuristic + ML ranking of task‑employee mapping; confidence score output.
5. Budget Integration (Phase‑2)
   - Provide validated activity totals and evidence to Finance for estimation.
   - Expose APIs consumed by Budget services (monthly/quarterly windows).
6. Validation & Auditing (Phase‑2)
   - Track evidence presence, anomalies, and approval trails.
7. Advanced Analytics (Phase‑3)
   - Forecasting dashboards, trend analysis, and compliance KPIs.

## Non‑Functional Requirements
- Reliability: Background jobs retried and monitored; service health checks.
- Performance: Queries optimized with indexes and prefetch/select_related.
- Observability: Structured logs + admin reports.
- Security: Role‑based access; PII protected; least‑privilege for API keys.

## Acceptance Criteria (Phase checkpoints)
- P0: All duplicated code removed; tests green; legacy placed under `deprecated/`.
- P1: ≥80% auto‑link rate for meetings; review UI; basic analytics delivered.
- P2: Budget API consumed by Finance; 60% variance reduction; evidence validation ≥90%.
- P3: Forecast dashboards live; automation ≥95%.

## Out of Scope (now)
- Financial transactions storage (owned by Finance).
- Vendor‑specific meeting transcription ML (we consume via ai_services).
