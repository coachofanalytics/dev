# Employee Activity System (Management) – 03_ARCHITECTURE.md

## High‑Level Design (How to design)
```
management (app)
├─ models/base_models.py         # Base domain model mixins
├─ views/base_views.py           # Base view classes
├─ services/utilities_service.py # Shared utilities (DRY)
├─ templates/management/components/
│  └─ base_components.html       # Reusable UI components
├─ management/commands/
│  └─ consolidate_management_app.py
└─ tests/test_consolidated_components.py
```

## Integrations
- ai_services
  - GoToMeeting integration (meeting metadata, recordings)
  - AI provider layer (RealAIService, configuration, health checker)
- finance
  - Budget estimation/validation services consume Management analytics

## Data Model (logical)
- Department, Category, Task (normalized)
- TaskHistory (activity events, sources)
- Evidence (meeting link, transcript ref, document ref)
- AssignmentScore (task ↔ employee confidence)

## Key Flows
1. Ingest meeting/task data → normalize → store TaskHistory/Evidence.
2. Link meetings to tasks (heuristic + ML) → AssignmentScore.
3. Expose analytics to Finance (rolling windows, category totals).
4. Validation: evidence completeness + anomaly flags.

## Boundaries & Contracts
- Service layer returns DTOs; no cross‑app ORM leakage.
- APIs return stable JSON envelopes with `data`, `meta`, `errors`.

## Performance Considerations
- Use `select_related/prefetch_related` for dashboard views.
- Add indexes on `(department_id, category_id, occurred_at)` in TaskHistory.

## Security
- Staff/manager roles for write; read limited by department.
- External credentials housed in env vars (never in repo).
