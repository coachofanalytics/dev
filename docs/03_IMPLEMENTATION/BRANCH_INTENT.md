# Branch Intent Documentation

## Branch Strategy for Career Ladder Implementation

This document describes the purpose and deployment status of branches created for the career ladder system implementation.

### 26.01_CODA_DEV_CM

**Purpose:** Development branch for all code changes and documentation related to the career ladder system.

**Contains:**
- All model changes (TaskGroups, UserProfile)
- All migrations (data and schema)
- Career ladder service and configuration
- Management commands
- Template/view updates
- Documentation

**Deployment:** Local development only. DO NOT deploy to Heroku.

**Status:** Active development branch.

---

### 26.01_CODA_UAT_CM

**Purpose:** UAT branch with minimal code appropriate for the UAT Heroku app (codamakutano).

**Contains:**
- Required code changes for UAT testing
- Minimal migrations needed for UAT
- Career ladder service (read-only operations for testing)

**Deployment:** Target Heroku app: `codamakutano` (UAT). **DO NOT DEPLOY YET** - wait for approval.

**Status:** Prepared but not deployed.

---

### 26.01_CODA_PROD_CM

**Purpose:** Production-ready code only, targeting the production Heroku app (codatrainingapp).

**Contains:**
- Production-safe model changes
- Production migrations
- Career ladder service (production-ready)
- No development/debugging code

**Deployment:** Target Heroku app: `codatrainingapp` (Production). **DO NOT DEPLOY YET** - requires explicit approval and staging verification.

**Status:** Prepared but not deployed.

---

## Important Notes

1. **DO NOT DEPLOY PRODUCTION BRANCH** (`26.01_CODA_PROD_CM`) to Heroku production (`codatrainingapp`) until:
   - All acceptance tests pass
   - UAT verification is complete
   - Explicit approval from stakeholders
   - Database backup is confirmed

2. **All branches are created from** `25.12_CODA_DEV_CM` HEAD unless otherwise stated.

3. **Backward Compatibility:** All changes preserve existing Group A..I rows and maintain compatibility with legacy `employee_group_level` logic.

4. **Policy Groups:** Career ladder is separate from policy groups (Group A/B/C for compliance). PolicyResolver behavior is unchanged.

---

## Deployment Checklist (When Ready)

- [ ] Run Phase 0 audit script and verify results
- [ ] Run migrations on cloned production database
- [ ] Verify TaskGroups existing rows (Group A..I) still exist with same IDs
- [ ] Verify UserProfile.career_group is set for all staff
- [ ] Run `diagnose_career_ladder` command and verify output
- [ ] Test DAF v2 pages load correctly
- [ ] Verify PolicyResolver behavior unchanged
- [ ] Test sample users (eunice, makied, KEN, idah_w) show ladder badge
- [ ] Database backup confirmed
- [ ] Stakeholder approval obtained

---

**Last Updated:** 2026-01-01
**Branch Creator:** Career Ladder Implementation Team

