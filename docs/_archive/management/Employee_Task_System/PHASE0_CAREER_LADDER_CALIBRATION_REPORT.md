# Phase 0 Career Ladder Calibration Report

**Report Date:** [YYYY-MM-DD]  
**Analysis Window:** [N] days (from [START_DATE] to [END_DATE])  
**Dataset Variant:** [All Active Staff / Excluding SPECIAL / Curated Cohort]  
**Approval Definition:** [Definition used]

---

## Executive Summary

This report presents a read-only diagnostic analysis of historical TaskHistory data to support dynamic boundary recommendations for the career ladder system. The analysis separates career progression metrics (cumulative lifetime points) from performance metrics (monthly/rolling) and generates boundary candidate schemes that are robust and prevent overly rapid promotions.

**Key Findings:**
- [Summary of key metrics]
- [Number of employees analyzed]
- [Total TaskHistory rows in scope]
- [Main boundary recommendations]

---

## Data Sources & Definitions

### Approval Definition
**Definition Used:** [CONSERVATIVE PROXY: TaskHistory.point > 0 AND TaskHistory.submission is not null]

**Rationale:** [Explanation of why this definition was chosen]

### What Counts Toward Career Progression
- **Source:** TaskHistory records
- **Filter:** `point > 0` AND `submission is not null`
- **Time Window:** Last [N] days
- **Employee Filter:** Active staff only (`is_staff=True` AND `is_active=True`)

### Special Exclusions
- **SPECIAL Groups:** [List of excluded groups, e.g., Group H, Group I]
- **Rationale:** SPECIAL groups are not part of the standard career ladder progression

### Dataset Variants Analyzed
1. **All Active Staff:** All employees matching staff/active criteria
2. **Excluding SPECIAL:** Same as above, but excluding TaskHistory records with SPECIAL groups
3. **Curated Cohort:** [If applicable, list usernames or reference to cohort file]

---

## Integrity Checks

### Data Quality Metrics
- **TaskHistory with NULL employee:** [count]
- **TaskHistory with NULL daf_date:** [count]
- **TaskHistory with NULL point:** [count]
- **Staff without profile:** [count]
- **Staff profiles without career_group:** [count]

### TaskHistory.group Distribution
| Group | Count |
|-------|-------|
| Group A | [count] |
| Group B | [count] |
| ... | ... |

### SPECIAL Groups Verification
- **Group H:** [is_special status, usage count]
- **Group I:** [is_special status, usage count]

---

## Core Distributions

### 4.1 Career Ladder Core (Cumulative Lifetime Points)

**Distribution of Total Cumulative Points Per Employee:**

| Metric | Value |
|--------|-------|
| Employees with points | [count] |
| Min | [value] |
| P10 | [value] |
| P25 | [value] |
| P50 (Median) | [value] |
| P75 | [value] |
| P90 | [value] |
| P95 | [value] |
| P99 | [value] |
| Max | [value] |
| Mean | [value] |

**Interpretation:** [Brief interpretation of distribution]

### 4.2 Time-to-Threshold Analysis

**Months to Reach Key Thresholds:**

| Threshold (Points) | Employees Reached | Median Months | P25 Months | P75 Months |
|-------------------|-------------------|---------------|-------------|------------|
| 350 | [count] | [value] | [value] | [value] |
| 800 | [count] | [value] | [value] | [value] |
| 1200 | [count] | [value] | [value] | [value] |
| 1600 | [count] | [value] | [value] | [value] |

**Interpretation:** [Analysis of progression speed]

### 4.3 Points Per Active Month

**Distribution of Points Per Active Month:**

| Metric | Value |
|--------|-------|
| Employees with active months | [count] |
| Min points/month | [value] |
| P50 (Median) | [value] |
| P75 | [value] |
| P90 | [value] |
| Max points/month | [value] |

### 4.4 Performance Metrics (Monthly & Rolling)

**NOTE:** These are performance metrics, NOT career progression.

**Monthly Points Distribution (All Employee-Months):**

| Metric | Value |
|--------|-------|
| Employee-months with points > 0 | [count] |
| Min monthly points | [value] |
| P50 (Median) | [value] |
| P75 | [value] |
| P90 | [value] |
| Max monthly points | [value] |

**Rolling 3-Month Sums:** [If calculated]
**Rolling 6-Month Sums:** [If calculated]

---

## Time-to-Threshold Findings

### Key Insights
- [Insight 1]
- [Insight 2]
- [Insight 3]

### Recommendations
- [Recommendation based on time-to-threshold data]

---

## Boundary Candidate Schemes

### SCHEME A: Percentile-Based (Robust)

**Rationale:** Uses percentiles of cumulative totals to reduce sensitivity to outliers.

| Track | Point Range | Percentile Cutoff |
|-------|-------------|-------------------|
| FOUNDATION | 0 - [P25] | P25 |
| GROWTH | [P25] - [P60] | P25-P60 |
| PROFESSIONAL | [P60] - [P85] | P60-P85 |
| ADVANCED | [P85] - [P95] | P85-P95 |
| LEAD | [P95]+ | P95+ |

**Numeric Cutoffs:**
- FOUNDATION: 0 - [value] points
- GROWTH: [value] - [value] points
- PROFESSIONAL: [value] - [value] points
- ADVANCED: [value] - [value] points
- LEAD: [value]+ points

### SCHEME B: Time-to-Threshold-Driven

**Rationale:** Selects boundaries based on median months-to-reach to control promotion speed.

| Threshold | Median Months to Reach | Recommended Boundary |
|-----------|------------------------|---------------------|
| [value] points | [value] months | [recommendation] |
| [value] points | [value] months | [recommendation] |

**Proposed Boundaries:**
- [Boundary 1]
- [Boundary 2]
- [Boundary 3]

### SCHEME C: Hybrid Guardrails

**Rationale:** Starts with Scheme A cutoffs, then applies guardrails to prevent rapid promotions.

**Guardrails Applied:**
- Minimum active months for FOUNDATION exit: [N] months
- Minimum active months for LEAD entry: [N] months

**Impact:**
- Employees blocked from FOUNDATION exit: [count]
- Employees blocked from LEAD entry: [count]

**Adjusted Boundaries:**
- [Same as Scheme A, with guardrail notes]

---

## Simulation Results (Promotion Speed)

### Track Change Frequency

| Metric | Value |
|--------|-------|
| Employees with track changes | [count] |
| Median gap between track changes | [value] months |
| Min gap | [value] months |
| P25 gap | [value] months |
| P75 gap | [value] months |

### Fast Promotions (< 2 months between changes)

**Count:** [count]

**Top Examples:**
| Username | Gap (Months) | Total Changes |
|----------|---------------|--------------|
| [username] | [value] | [count] |
| [username] | [value] | [count] |

### Analysis
[Interpretation of simulation results]

---

## Outliers & Risk Notes

### Top 1% Monthly Spikes

| Username | Month | Points |
|----------|-------|--------|
| [username] | [YYYY-MM] | [value] |
| [username] | [YYYY-MM] | [value] |

### Zero-Stretch Then Spike Pattern

**Employees with 3+ consecutive zero months followed by spike:**

| Username | Zero Months | Spike Points |
|----------|-------------|--------------|
| [username] | [count] | [value] |
| [username] | [count] | [value] |

### Risk Assessment
- [Risk note 1]
- [Risk note 2]
- [Risk note 3]

---

## This Month vs Last Month Comparison

**Last Month Report Date:** [YYYY-MM-DD]  
**This Month Report Date:** [YYYY-MM-DD]

### Changes in Key Metrics

| Metric | Last Month | This Month | Change |
|--------|------------|------------|--------|
| Active staff count | [value] | [value] | [±value] |
| TaskHistory rows | [value] | [value] | [±value] |
| Median cumulative points | [value] | [value] | [±value] |
| P95 cumulative points | [value] | [value] | [±value] |

### Boundary Recommendations Comparison

**Last Month Scheme A:**
- FOUNDATION: 0 - [value]
- GROWTH: [value] - [value]
- ...

**This Month Scheme A:**
- FOUNDATION: 0 - [value]
- GROWTH: [value] - [value]
- ...

**Changes:** [Summary of boundary shifts]

---

## Next Implementation Options

### Option 1: Implement Dynamic Boundaries
- [Description]
- [Pros/Cons]
- [Implementation complexity]

### Option 2: Quarterly Recalibration
- [Description]
- [Pros/Cons]
- [Implementation complexity]

### Option 3: Hybrid Approach
- [Description]
- [Pros/Cons]
- [Implementation complexity]

### Recommended Next Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

---

## Appendix

### Command Used to Generate This Report

```bash
python manage.py diagnose_career_ladder_calibration \
  --days 730 \
  --exclude-special true \
  --min-active-months 3
```

### Configuration
- **Days Window:** [value]
- **Exclude SPECIAL:** [true/false]
- **Min Active Months:** [value]
- **Cohort File:** [path or N/A]

### Data Export
[If JSON export was generated, reference location]

---

**Report Generated:** [YYYY-MM-DD HH:MM:SS]  
**Generated By:** [System/User]  
**Next Review Date:** [YYYY-MM-DD]

