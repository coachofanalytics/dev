# Task Reset Scheduling Options - Discussion

## Current Situation
- Task reset is **manual** via `/management/reset_tasks/`
- Tasks were reset on Nov 4th (arbitrary date)
- `daf_date` was NULL, causing payroll display issues
- There's a commented-out Celery schedule for 1st of month (not active)

---

## Option 1: Reset on 1st of New Month (Recommended)

### How It Works
- **When:** Automated on 1st of each month at midnight (00:00)
- **What happens:**
  1. All tasks from previous month → moved to TaskHistory
  2. `daf_date` = last day of previous month (e.g., Oct 31) OR same day of last month
  3. Task points reset to 0
  4. New month starts fresh

### Pros ✅
- **Clean start:** New month begins with clean slate
- **Predictable:** Always happens on 1st, easy to plan around
- **Semantic clarity:** `daf_date` represents "when work was done" (last month)
- **Payroll alignment:** Viewing last month shows all completed work
- **No date manipulation needed:** `daf_date` naturally = last month

### Cons ❌
- **Timing risk:** If run too early (before month ends), might miss last-day work
- **Need to ensure it runs:** Requires Celery Beat to be active
- **Manual override:** Still need manual reset option for edge cases

### Implementation
```python
# In coda/coda_project/celery.py
app.conf.beat_schedule = {
    'monthly_task_reset': {
        'task': 'task_history',  # dump_data function
        'schedule': crontab(hour=0, minute=0, day_of_month='1'),  # 1st at midnight
    },
}
```

### daf_date Logic
```python
# In dump_data()
current_date = date.today()  # Nov 1
last_month = current_date - relativedelta(months=1)  # October
# Option A: Last day of last month
daf_date = date(last_month.year, last_month.month, calendar.monthrange(last_month.year, last_month.month)[1])  # Oct 31
# Option B: Same day of last month (if reset on 1st, this would be Oct 1)
daf_date = date(last_month.year, last_month.month, 1)  # Oct 1
```

---

## Option 2: Reset at End of Month

### How It Works
- **When:** Automated on last day of month (e.g., Oct 31 at 23:59)
- **What happens:**
  1. All tasks from current month → moved to TaskHistory
  2. `daf_date` = current month (e.g., Oct 31 = October)
  3. Task points reset to 0
  4. Next day (Nov 1) starts fresh

### Pros ✅
- **Natural date:** `daf_date` = actual month work was done (no manipulation)
- **Complete month:** Captures all work from the full month
- **Simpler logic:** No need to calculate "last month"

### Cons ❌
- **Timing critical:** Must run before month ends (or miss data)
- **Edge case:** What if system is down on last day?
- **Payroll timing:** If viewing payroll on 1st, data might not be ready yet
- **Timezone issues:** Last day varies by timezone

### Implementation
```python
# In coda/coda_project/celery.py
app.conf.beat_schedule = {
    'monthly_task_reset': {
        'task': 'task_history',
        'schedule': crontab(hour=23, minute=59, day_of_month='28-31'),  # Last day
    },
}
```

### daf_date Logic
```python
# In dump_data()
current_date = date.today()  # Oct 31
# daf_date = current month (when work was done)
daf_date = date(current_date.year, current_date.month, current_date.day)  # Oct 31
# OR use last day of current month
last_day = calendar.monthrange(current_date.year, current_date.month)[1]
daf_date = date(current_date.year, current_date.month, last_day)  # Oct 31
```

---

## Recommendation: **Option 1 (Reset on 1st)**

### Why?
1. **More reliable:** Running on 1st gives buffer - if it fails, can manually run
2. **Clear semantics:** `daf_date` = "work done in previous month" is intuitive
3. **Payroll alignment:** When viewing October payroll, all October work is there
4. **Less timezone sensitive:** 1st of month is clear regardless of timezone
5. **Matches current expectation:** Users expect to see last month's work when viewing last month

### Implementation Plan

#### Step 1: Update `dump_data()` to handle 1st-of-month reset
```python
def dump_data(request):
    current_date = date.today()
    
    # If running on 1st of month, daf_date = last day of previous month
    if current_date.day == 1:
        last_month = current_date - relativedelta(months=1)
        last_day = calendar.monthrange(last_month.year, last_month.month)[1]
        default_daf_date = date(last_month.year, last_month.month, last_day)
    else:
        # Manual reset (not on 1st) - use same day of last month
        default_daf_date = current_date - relativedelta(months=1)
    
    # ... rest of logic
```

#### Step 2: Enable Celery schedule
```python
# In coda/coda_project/celery.py
app.conf.beat_schedule = {
    'monthly_task_reset': {
        'task': 'task_history',
        'schedule': crontab(hour=0, minute=0, day_of_month='1'),
    },
}
```

#### Step 3: Keep manual reset option
- Still allow manual reset via `/management/reset_tasks/`
- Manual reset should use same logic (set daf_date to last month)

---

## Alternative: Hybrid Approach

### Reset Window: Last 3 days of month OR 1st of month
- **Try to reset on last day** (captures full month)
- **Fallback to 1st** if last-day reset failed
- **Manual override** always available

```python
# Celery schedule
app.conf.beat_schedule = {
    'monthly_task_reset_attempt_1': {
        'task': 'task_history',
        'schedule': crontab(hour=23, minute=0, day_of_month='28-31'),  # Try last 3 days
    },
    'monthly_task_reset_attempt_2': {
        'task': 'task_history',
        'schedule': crontab(hour=0, minute=0, day_of_month='1'),  # Fallback on 1st
    },
}
```

---

## Decision Needed

**Questions to answer:**
1. When should payroll for October be finalized? (End of Oct or start of Nov?)
2. Do we need to capture work done on the last day of the month?
3. What happens if automated reset fails? (Manual backup needed?)
4. Should `daf_date` represent "work done date" or "payroll period"?

**Recommendation:** Go with **Option 1 (Reset on 1st)** for reliability and clarity.

