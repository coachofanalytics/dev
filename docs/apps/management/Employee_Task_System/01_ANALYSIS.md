# Employee Activity System (Management) – 01_ANALYSIS.md

## Purpose (Why)
The Management app powers the Employee Activity System (DAF) – a data‑driven layer that correlates tasks, meetings and department activities to surface insights, automate evidence, and prepare reliable inputs for budgeting and performance management.

## Problem Statement
- Fragmented utilities and repeated patterns across views/services (pre Phase‑0) created high maintenance cost and slow iteration.
- Evidence collection for tasks (meetings, artifacts) is largely manual and error‑prone.
- No unified, historical view to quantify activity → poor inputs for budget planning and staff performance.

## Goals
- Create a consolidated, DRY foundation for the app (Phase‑0 – DONE).
- Shift to a data‑driven system using TaskHistory and meeting artifacts.
- Automate evidence capture (GoToMeeting, Docs) and assignment with ML heuristics.
- Provide reliable analytics to Finance (Budget estimation, validation).

## Scope
- Management app only; integrates with `ai_services` (GoToMeeting, AI provider layer) and `finance` (Budget).
- Users: staff, managers and system services.

## Current State (October 2025)
- Phase‑0 consolidation deployed to UAT (v800). Six consolidated components, legacy isolated under `deprecated/`.
- Clean folder structure: base models/views, shared components, utilities service, tests and a consolidation command.
- Phase‑1 quick wins ready to start (data analysis + automation + basic AI matching).

## Key Pain Points Identified
- Repeated utility logic across modules → fixed via `services/utilities_service.py`.
- Template/UI duplication → reusable `templates/management/components/`.
- Weak data feedback loop → plan to leverage TaskHistory + meeting data.

## Success Metrics (targets)
- Phase‑1: 80% meetings auto‑linked to tasks; 70% improvement in task‑employee matching.
- Phase‑2: 60% reduction in budget variances; 75% accuracy in budget predictions; 90% evidence validation accuracy.
- Phase‑3: 95% process automation; 80% accuracy in 3‑month forecasts.

## Risks & Mitigations
- Data quality variance → institute validation jobs and backfills.
- Service health (GoToMeeting/AI) → add `AIHealthChecker` monitoring and fallbacks.
- Cross‑app coupling → keep integration via service boundaries and DTOs.

## References
- Employee_Activity_System_Analysis.md (deep‑dive)
- Data_Driven_System_Enhancement_Plan.md (approach & ML)
- Comprehensive_Implementation_Guide.md (roadmap)
system will:
Convert those approved suggestions to pending OptionsPosition records.