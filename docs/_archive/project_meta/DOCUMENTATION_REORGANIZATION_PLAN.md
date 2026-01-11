# Documentation Reorganization Plan - January 2026

**Date:** January 2, 2026  
**Purpose:** Move root-level documentation files to their respective app/feature locations

---

## Files to Move

### Management App - Employee Task System

| File | Current Location | Target Location | Reason |
|------|-----------------|-----------------|--------|
| `PHASE0_EVIDENCE_MEETING_MATCHING_REPORT.md` | `docs/` | `docs/apps/management/Employee_Task_System/` | Evidence/Meeting matching diagnostic for DAF |
| `PHASE0_EVIDENCE_MATCHING_REPORT.md` | `docs/` | `docs/apps/management/Employee_Task_System/` | Evidence matching diagnostic for DAF |
| `PHASE0_CAREER_LADDER_CALIBRATION_REPORT.md` | `docs/` | `docs/apps/management/Employee_Task_System/` | Career ladder calibration analysis |
| `MANUAL_TEST_CHECKLIST_26_01_CAREER_LADDER.md` | `docs/` | `docs/04_TESTING/` or `docs/apps/management/Employee_Task_System/` | Career ladder testing checklist |
| `AI_REQUIREMENT_MATCHING_IMPLEMENTATION.md` | `docs/` | `docs/apps/management/Employee_Task_System/` | AI requirement matching (used by DAF) |

### AI Services App - GoToMeeting

| File | Current Location | Target Location | Reason |
|------|-----------------|-----------------|--------|
| `MEETING_DATA_HYGIENE_QUICK_START.md` | `docs/` | `docs/apps/ai_services/GoToMeeting/` | Meeting data hygiene guide |
| `MEETING_DATA_HYGIENE_REPORT.md` | `docs/` | `docs/apps/ai_services/GoToMeeting/` | Meeting data hygiene report |
| `MEETING_SYNC_OPERATIONS.md` | `docs/` | `docs/apps/ai_services/GoToMeeting/` | Meeting sync operations |

### AI Services App - General

| File | Current Location | Target Location | Reason |
|------|-----------------|-----------------|--------|
| `AI_INFRA_AUDIT.md` | `docs/` | `docs/apps/ai_services/` | AI infrastructure audit |
| `AI_OPS_RUNBOOK.md` | `docs/` | `docs/apps/ai_services/` or `docs/07_MAINTENANCE/` | AI operations runbook |

### Implementation/Infrastructure

| File | Current Location | Target Location | Reason |
|------|-----------------|-----------------|--------|
| `BRANCH_INTENT.md` | `docs/` | `docs/03_IMPLEMENTATION/` | Branch management strategy |

### Documentation Meta (Keep or Archive)

| File | Current Location | Target Location | Reason |
|------|-----------------|-----------------|--------|
| `DOCUMENTATION_CONSOLIDATION_COMPLETE.md` | `docs/` | Keep in root or move to `docs/_archive/project_meta/` | Meta-documentation |
| `DOCUMENTATION_ORGANIZATION_ROUND*.md` | `docs/` | Move to `docs/_archive/project_meta/` | Historical organization rounds |
| `DOCUMENTATION_REORGANIZATION_2025.md` | `docs/` | Move to `docs/_archive/project_meta/` | Historical reorganization |

---

## Execution Plan

1. Create target directories if they don't exist
2. Move files to their target locations
3. Update any cross-references if needed
4. Create summary of moves

---

**Status:** Ready for execution

