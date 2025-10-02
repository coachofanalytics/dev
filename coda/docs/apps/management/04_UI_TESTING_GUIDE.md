# Management App - Comprehensive UI Testing Guide

## Overview
This guide provides step-by-step instructions for testing all management app features from a **user perspective** (not developer perspective). All testing starts from the main dashboard.

**Entry Point:** https://codamakutano.herokuapp.com/dashboard/

---

## Prerequisites

### User Roles Required for Testing
1. **Employee User** - For testing task management, payroll, evidence submission
2. **Manager/Supervisor** - For testing task assignment, team oversight
3. **Admin User** - For testing system-wide features, analytics, and AI features

### Test Accounts
Make sure you have credentials for all three user types before starting.

---

## Phase 0: Core Task Management Features

### 1. Task Management Testing

#### Access Points:
- **Dashboard:** https://codamakutano.herokuapp.com/dashboard/
- **Task List:** https://codamakutano.herokuapp.com/management/tasks/
- **User Tasks:** Navigate from dashboard → "My Tasks" or "Tasks"

#### Test Scenarios:

**A. View Tasks (Employee Perspective)**
1. Login as an employee
2. Navigate to "My Tasks" from dashboard
3. **Verify:**
   - All assigned tasks are visible
   - Task details show: title, category, group, due date, points
   - Task status is clearly indicated
   - Can filter by status (pending, in progress, completed)

**B. Submit Task Evidence**
1. From task list, click on a specific task
2. Click "Submit Evidence" or "New Evidence"
3. **Verify:**
   - Can upload files/documents
   - Can add text descriptions
   - Can attach photos/screenshots
   - Evidence submission confirms successfully
   - Evidence appears in task detail page

**C. Update Task Status**
1. Navigate to a task
2. Click "Update" or "Edit"
3. Change status (e.g., from "Pending" to "In Progress")
4. **Verify:**
   - Status updates successfully
   - Updated status reflects immediately
   - Task appears in correct filter category

**D. Create New Tasks (Manager Perspective)**
1. Login as manager/supervisor
2. Navigate to "New Task" or "Create Task"
3. Fill in task details:
   - Task title
   - Category/Department
   - Task group
   - Assignee (employee)
   - Due date
   - Target points
4. **Verify:**
   - Task creates successfully
   - Assigned employee can see task
   - Task appears in correct category

---

### 2. Payroll & Compensation Testing

#### Access Points:
- **Payroll View:** https://codamakutano.herokuapp.com/management/payroll/
- **Dashboard:** Navigate from main menu → "Payroll" or "My Pay"

#### Test Scenarios:

**A. View Payslip (Employee Perspective)**
1. Login as employee
2. Navigate to "Payroll" or "My Payslip"
3. Select month and year
4. **Verify:**
   - Payslip displays correctly
   - Shows: basic salary, allowances, deductions, net pay
   - Task-based earnings are calculated correctly
   - Can download/print payslip

**B. Review Compensation Breakdown**
1. From payslip view
2. **Verify:**
   - Fixed salary component is correct
   - Task-based pay reflects completed tasks
   - Deductions (taxes, insurance) are accurate
   - Total compensation adds up correctly

**C. Historical Payroll Review**
1. Navigate to payroll history
2. Select different months
3. **Verify:**
   - Can view past payslips
   - Data is consistent across months
   - Year-to-date totals are accurate

---

### 3. Employee Contract & Policies Testing

#### Access Points:
- **Contracts:** https://codamakutano.herokuapp.com/management/employee_contract/
- **Policies:** https://codamakutano.herokuapp.com/management/policies/

#### Test Scenarios:

**A. View & Confirm Contract**
1. Login as new employee
2. Navigate to "Employee Contract"
3. **Verify:**
   - Contract displays correctly
   - All terms and conditions are readable
   - Can confirm/accept contract
   - Confirmation is recorded

**B. Review Company Policies**
1. Navigate to "Policies" from menu
2. **Verify:**
   - All company policies are listed
   - Can view policy details
   - Policies are categorized properly
   - Can download policy documents

---

### 4. Performance Assessment Testing

#### Access Points:
- **Score Report:** https://codamakutano.herokuapp.com/management/score_report/
- **Assessment:** https://codamakutano.herokuapp.com/management/assessment/{user_type}

#### Test Scenarios:

**A. View Performance Score (Employee Perspective)**
1. Login as employee
2. Navigate to "Score Report" or "My Performance"
3. **Verify:**
   - Current performance score is visible
   - Score breakdown by category
   - Historical performance trends
   - Comparison to targets/goals

**B. Team Assessment (Manager Perspective)**
1. Login as manager
2. Navigate to "Team Assessment"
3. **Verify:**
   - Can see all team members
   - Performance scores for each member
   - Can filter/sort by various metrics
   - Can drill down to individual assessments

---

## Phase 1: Data Analysis & Insights

### 5. Performance Analytics Testing

#### Access via Management Commands (Admin Only):

Since the web UI routes are temporarily disabled, test these features via Heroku CLI:

```bash
# Connect to Heroku app
heroku run bash --app codamakutano

# Analyze TaskHistory data
python coda/manage.py analyze_task_history

# Validate data quality
python coda/manage.py validate_data_quality
```

#### Expected Outputs:

**A. TaskHistory Analysis**
- **Employee Performance Analysis:** Top performers, completion rates, earning efficiency
- **Department Performance:** Department rankings, workload distribution
- **Category Performance:** Most productive categories, bottlenecks
- **Earning Analysis:** Salary vs. task earnings breakdown
- **Insights & Recommendations:** Actionable insights based on data

**B. Data Quality Validation**
- NULL date detection and counts
- Division by zero warnings
- Data completeness scores
- Recommendations for data cleanup

---

## Phase 2: AI-Powered Features

### 6. AI Performance Predictions Testing

#### Access via Management Commands:

```bash
# Test AI prediction service
heroku run python coda/manage.py test_ai_predictions --app codamakutano
```

#### Expected Outputs:

**A. Individual Performance Predictions**
- Next month's expected task completion rate
- Predicted earnings
- Risk assessment (overwork/underperformance)
- Confidence scores

**B. Department-Level Predictions**
- Department productivity forecasts
- Resource allocation recommendations
- Workload balancing suggestions

**C. Task Completion Predictions**
- Probability of task completion on time
- Risk factors for delays
- Recommended interventions

---

### 7. Intelligent Task Assignment Testing

#### Access via Management Commands:

```bash
# Test intelligent assignment
heroku run python coda/manage.py test_intelligent_assignment --app codamakutano
```

#### Expected Outputs:

**A. Workload-Based Assignment**
- Assigns tasks to employees with available capacity
- Balances workload across team
- Considers employee skills/categories

**B. Skill-Based Assignment**
- Matches tasks to employee expertise
- Considers past performance in similar tasks
- Optimizes for best outcome

**C. Performance-Based Assignment**
- Routes tasks to high performers for critical work
- Provides development opportunities to others
- Maintains fairness in distribution

**D. Batch Assignment**
- Assigns multiple tasks simultaneously
- Optimizes entire team's workload
- Minimizes conflicts and overload

---

### 8. Comprehensive Phase 2 Testing

#### Access via Management Commands:

```bash
# Run complete Phase 2 test suite
heroku run python coda/manage.py test_phase2_comprehensive --app codamakutano
```

#### Expected Outputs:

This comprehensive test validates:
1. ✅ **Data Validation Service** - Data quality checks pass
2. ✅ **AI Prediction Service** - Predictions generate successfully
3. ✅ **Intelligent Assignment** - All assignment strategies work
4. ✅ **Department Optimization** - Resource optimization recommendations
5. ✅ **Real-time Monitoring** - Alert system functions correctly

---

## Admin Panel Testing

### 9. Django Admin Interface Testing

#### Access Point:
- **Admin Panel:** https://codamakutano.herokuapp.com/admin/

#### Test Scenarios:

**A. Task Management**
1. Login to admin panel
2. Navigate to "Management" → "Tasks"
3. **Verify:**
   - Can view all tasks
   - Can filter by employee, status, category
   - Can edit task details
   - Can bulk update tasks

**B. Employee Management**
1. Navigate to "Accounts" → "Users" or "Customer Users"
2. **Verify:**
   - Can view all employees
   - Can see employee details (category, department, salary)
   - Can update employee information
   - Can filter by various criteria

**C. TaskHistory Analysis**
1. Navigate to "Management" → "Task History"
2. **Verify:**
   - Historical task data is present
   - Data includes all required fields (daf_date, employee, points, etc.)
   - Can filter by date range, employee, department

**D. Payroll Data**
1. Navigate to relevant payroll models
2. **Verify:**
   - Payroll calculations are stored correctly
   - Can view payroll history
   - Data integrity is maintained

---

## Testing Checklist

### Phase 0: Core Features ✅
- [ ] Employee can view assigned tasks
- [ ] Employee can submit task evidence
- [ ] Employee can update task status
- [ ] Manager can create and assign tasks
- [ ] Employee can view payslip
- [ ] Payroll calculations are accurate
- [ ] Employee can view and confirm contract
- [ ] Company policies are accessible
- [ ] Performance scores display correctly
- [ ] Manager can view team assessments

### Phase 1: Data Analysis ✅
- [ ] TaskHistory analysis runs successfully
- [ ] Employee performance insights are generated
- [ ] Department performance analysis works
- [ ] Data quality validation detects issues
- [ ] Insights and recommendations are actionable

### Phase 2: AI Features ✅
- [ ] AI predictions generate for employees
- [ ] Department predictions are accurate
- [ ] Intelligent assignment distributes tasks fairly
- [ ] Workload-based assignment prevents overload
- [ ] Skill-based assignment matches expertise
- [ ] Comprehensive tests pass all validations

### Admin Panel ✅
- [ ] Can manage tasks via admin panel
- [ ] Can manage employees via admin panel
- [ ] TaskHistory data is complete and accurate
- [ ] Payroll data is accessible and correct

---

## Troubleshooting

### Common Issues and Solutions

**Issue: Cannot access management URLs**
- **Solution:** Ensure you're logged in with correct user role
- **Solution:** Check that URL includes full path: `/management/tasks/` not `/tasks/`

**Issue: Payslip doesn't display**
- **Solution:** Ensure TaskHistory data exists for selected month
- **Solution:** Run data validation: `python coda/manage.py validate_data_quality`

**Issue: Tasks not showing**
- **Solution:** Verify tasks are assigned to logged-in employee
- **Solution:** Check task status filters (may be filtering out tasks)

**Issue: AI predictions fail**
- **Solution:** Ensure sufficient historical data (minimum 30 days recommended)
- **Solution:** Run data quality validation first
- **Solution:** Check Heroku logs: `heroku logs --tail --app codamakutano`

**Issue: Management commands timeout**
- **Solution:** Use larger Heroku dyno size temporarily
- **Solution:** Run during off-peak hours
- **Solution:** Break analysis into smaller date ranges

---

## Next Steps After Testing

1. **Document Issues:** Note any bugs or unexpected behavior
2. **Collect Feedback:** Gather user feedback on UI/UX
3. **Performance Metrics:** Monitor page load times and query performance
4. **Data Validation:** Ensure all data is accurate and complete
5. **Training Materials:** Create user guides based on testing experience

---

## Support

For issues or questions during testing:
- **Technical Issues:** Check Heroku logs or Django admin logs
- **Data Issues:** Run validation commands
- **UI/UX Issues:** Document and report for Phase 3 improvements

---

## Summary

This UI testing guide covers:
- ✅ **Core Task Management:** Task creation, assignment, evidence submission
- ✅ **Payroll & Compensation:** Payslip viewing, calculation verification
- ✅ **Performance Assessment:** Score reports, team assessments
- ✅ **Data Analysis:** Historical analysis, insights generation
- ✅ **AI Features:** Predictions, intelligent assignment, optimization
- ✅ **Admin Tools:** Django admin interface for system management

All features are accessible from the main dashboard at https://codamakutano.herokuapp.com/dashboard/ and tested from a **user perspective**, not a developer perspective.

