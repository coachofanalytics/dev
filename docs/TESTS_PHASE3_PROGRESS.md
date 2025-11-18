# CODA Testing Phase 3 – In Progress

**Date:** November 10, 2025  
**Owner:** Cursor AI + CODA QA  
**Phase Focus:** Performance + Expanded Workflows + Security Hardening

---

## ✅ Completed This Pass

- **Performance Baselines Established**
  - `tests/investing/03_performance/test_query_performance.py` – caps client portal at ≤12 queries, preventing N+1 regressions.  
  - `tests/investing/03_performance/test_load_times.py` – enforces sub-500 ms render target for the client portal.
  - `tests/finance/03_performance/test_query_performance.py` – keeps budget request index at ≤11 queries with heavy data.  
  - `tests/finance/03_performance/test_load_times.py` – asserts budget request list response <500 ms.
- **Managed Trading Portal Optimization**
  - Updated `coda/investing/views/managed_trading/client.py` to eliminate redundant `positions.filter()` calls and replace `count()` with in-memory evaluation to keep query counts stable.

---

## 🧪 Upcoming Coverage (Phase 3 Backlog)

- **Integration & Regression Expansion (In Progress)**
  - Finance: approval escalations, disbursement hand-offs, REST endpoints.
  - Management: dashboard data integrity, training/Policy flows.
  - Portfolio: presentation assembly + registry discovery.
- **Security Hardening**
  - Finance dashboards: role gateway, data-scoping tests.
  - Management control panels: staff/admin segregation, inactive user blocking.
- **Manual Verification Workflow**
  - Execute every `07_manual` checklist.
  - Capture evidence (screenshots, CSVs) and store under `tests/<app>/07_manual/test_results/`.

---

## 📌 Test Commands

```bash
# Targeted performance suites
python coda/manage.py test tests.investing.03_performance
python coda/manage.py test tests.finance.03_performance

# Combined check (when migrations issue resolved)
python coda/manage.py test tests.investing.03_performance tests.finance.03_performance
```

> **Heads-up:** Current test run blocked by legacy migration reference to `accounts.CustomerUser`. Coordinate with data team to retire or stub the legacy model before attempting full suite runs.

---

## 🔄 Next Actions

1. Extend finance and management integration tests (phase3_integ).  
2. Implement finance + management security regression suites (phase3_security).  
3. Stand up manual execution log template + evidence collection workflow.  
4. Re-run combined performance suites after migration fix.

---

**Status:** Phase 3 underway – performance safeguards landed. Integration/security passes queued next.*** End Patch




