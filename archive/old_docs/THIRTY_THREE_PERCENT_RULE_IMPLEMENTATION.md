# 33% Completion Rule Implementation

## 🎯 **Business Rule**
*"For a new month, an employee must meet 33% of their activities by 15th of the month for the pay for last month to be approved"*

## 🏗️ **Implementation Strategy**

### **Integration Point: Budget Submission Level**
Instead of blocking during task migration, the 33% rule will be enforced when:
1. **Budget submissions** are prepared for approval
2. **Employee lists** are generated for payroll
3. **Non-compliant employees** receive email notifications
4. **Compliant employees** are submitted to budget system for approval

---

## 📊 **Current Budget Approval System Analysis**

### **Existing Components:**
- **BudgetEstimateProjection** - Budget projections awaiting approval
- **BudgetRequest** - Individual budget requests
- **ApprovalEngineService** - Handles approval workflows
- **Email notifications** - Already integrated for approvals

### **Integration Points:**
1. **`budget_projection_approvals`** - List pending approvals
2. **`submit_for_approval`** - Submit budget for approval
3. **`approve_budget_projection`** - Approve budget projections
4. **EmailService** - Send notifications

---

## 🔧 **Implementation Design**

### **1. Employee Compliance Checker Service**

```python
# management/services/employee_compliance_service.py
class EmployeeComplianceService:
    """
    Service to check employee compliance with 33% rule
    """
    
    def check_33_percent_compliance(self, employee, target_month, target_year):
        """
        Check if employee meets 33% completion rule for given month
        
        Args:
            employee: User object
            target_month: Month to check (previous month)
            target_year: Year to check
            
        Returns:
            dict: {
                'is_compliant': bool,
                'completion_rate': float,
                'total_tasks': int,
                'completed_tasks': int,
                'required_tasks': int,
                'missing_tasks': int
            }
        """
        
        # Get employee's tasks for the target month
        tasks = TaskHistory.objects.filter(
            employee=employee,
            daf_date__month=target_month,
            daf_date__year=target_year
        )
        
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(point__gt=0).count()
        
        # Calculate completion rate
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate required tasks (33% of total)
        required_tasks = int(total_tasks * 0.33)
        missing_tasks = max(0, required_tasks - completed_tasks)
        
        is_compliant = completion_rate >= 33.0
        
        return {
            'is_compliant': is_compliant,
            'completion_rate': completion_rate,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'required_tasks': required_tasks,
            'missing_tasks': missing_tasks
        }
    
    def get_department_compliance_report(self, department, target_month, target_year):
        """
        Get compliance report for entire department
        """
        employees = CustomerUser.objects.filter(
            is_staff=True,
            is_active=True,
            department=department
        )
        
        compliance_data = []
        compliant_count = 0
        
        for employee in employees:
            compliance = self.check_33_percent_compliance(employee, target_month, target_year)
            compliance_data.append({
                'employee': employee,
                'compliance': compliance
            })
            
            if compliance['is_compliant']:
                compliant_count += 1
        
        total_employees = employees.count()
        department_compliance_rate = (compliant_count / total_employees * 100) if total_employees > 0 else 0
        
        return {
            'department': department,
            'total_employees': total_employees,
            'compliant_employees': compliant_count,
            'non_compliant_employees': total_employees - compliant_count,
            'department_compliance_rate': department_compliance_rate,
            'employee_data': compliance_data
        }
```

### **2. Enhanced Budget Submission with Compliance Check**

```python
# finance/services/enhanced_budget_service.py
class EnhancedBudgetService(BaseFinanceService):
    """
    Enhanced budget service with 33% compliance checking
    """
    
    def __init__(self):
        super().__init__()
        self.compliance_service = EmployeeComplianceService()
        self.email_service = EmailService()
    
    def prepare_budget_submission_with_compliance(self, budget_data):
        """
        Prepare budget submission with 33% compliance validation
        
        Args:
            budget_data: Budget submission data
            
        Returns:
            dict: {
                'compliant_employees': list,
                'non_compliant_employees': list,
                'emails_sent': int,
                'budget_submission': BudgetEstimateProjection
            }
        """
        
        current_date = datetime.now()
        target_month = current_date.month - 1 if current_date.month > 1 else 12
        target_year = current_date.year if current_date.month > 1 else current_date.year - 1
        
        # Check if it's after 15th of current month
        is_after_15th = current_date.day > 15
        
        if not is_after_15th:
            # Before 15th - no compliance check needed
            return self._create_budget_submission(budget_data, all_employees=True)
        
        # After 15th - enforce 33% rule
        compliant_employees = []
        non_compliant_employees = []
        emails_sent = 0
        
        # Get all active employees
        all_employees = CustomerUser.objects.filter(is_staff=True, is_active=True)
        
        for employee in all_employees:
            compliance = self.compliance_service.check_33_percent_compliance(
                employee, target_month, target_year
            )
            
            if compliance['is_compliant']:
                compliant_employees.append({
                    'employee': employee,
                    'compliance': compliance
                })
            else:
                non_compliant_employees.append({
                    'employee': employee,
                    'compliance': compliance
                })
                
                # Send email notification
                self._send_compliance_notification(employee, compliance)
                emails_sent += 1
        
        # Create budget submission only with compliant employees
        budget_submission = self._create_budget_submission(
            budget_data, 
            compliant_employees=compliant_employees
        )
        
        return {
            'compliant_employees': compliant_employees,
            'non_compliant_employees': non_compliant_employees,
            'emails_sent': emails_sent,
            'budget_submission': budget_submission
        }
    
    def _send_compliance_notification(self, employee, compliance):
        """
        Send email notification to non-compliant employee
        """
        context = {
            'employee_name': employee.first_name,
            'completion_rate': compliance['completion_rate'],
            'total_tasks': compliance['total_tasks'],
            'completed_tasks': compliance['completed_tasks'],
            'required_tasks': compliance['required_tasks'],
            'missing_tasks': compliance['missing_tasks'],
            'current_date': datetime.now().strftime('%B %d, %Y'),
            'deadline': '15th of next month'
        }
        
        self.email_service.send_email(
            to_email=employee.email,
            subject='Action Required: Complete 33% of Tasks for Payroll Approval',
            template_name='management/email/compliance_notification.html',
            context=context
        )
```

### **3. Enhanced Budget Approval View**

```python
# finance/views_enhanced_approvals.py
@login_required
def enhanced_budget_projection_approvals(request):
    """
    Enhanced budget approval view with compliance checking
    """
    current_date = datetime.now()
    is_after_15th = current_date.day > 15
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'check_compliance':
            # Check compliance for all employees
            compliance_service = EmployeeComplianceService()
            target_month = current_date.month - 1 if current_date.month > 1 else 12
            target_year = current_date.year if current_date.month > 1 else current_date.year - 1
            
            # Get compliance report by department
            departments = Department.objects.filter(is_active=True)
            compliance_reports = []
            
            for department in departments:
                report = compliance_service.get_department_compliance_report(
                    department, target_month, target_year
                )
                compliance_reports.append(report)
            
            context = {
                'compliance_reports': compliance_reports,
                'target_month': target_month,
                'target_year': target_year,
                'is_after_15th': is_after_15th
            }
            
            return render(request, 'finance/approvals/compliance_report.html', context)
        
        elif action == 'submit_compliant_only':
            # Submit budget with only compliant employees
            budget_service = EnhancedBudgetService()
            result = budget_service.prepare_budget_submission_with_compliance(request.POST)
            
            messages.success(
                request,
                f'Budget submitted with {len(result["compliant_employees"])} compliant employees. '
                f'{len(result["non_compliant_employees"])} non-compliant employees notified via email.'
            )
            
            return redirect('finance:budget-projection-approvals')
    
    # Get existing projections
    projections = BudgetEstimateProjection.objects.filter(
        status='submitted'
    ).order_by('-submitted_at')
    
    context = {
        'projections': projections,
        'is_after_15th': is_after_15th,
        'current_date': current_date
    }
    
    return render(request, 'finance/approvals/enhanced_approvals.html', context)
```

### **4. Email Template for Non-Compliant Employees**

```html
<!-- management/templates/management/email/compliance_notification.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Action Required: Task Completion</title>
</head>
<body>
    <h2>Action Required: Complete 33% of Tasks for Payroll Approval</h2>
    
    <p>Dear {{ employee_name }},</p>
    
    <p>We hope this email finds you well. As part of our monthly payroll process, we need to inform you about your task completion status for last month.</p>
    
    <h3>Your Current Status:</h3>
    <ul>
        <li><strong>Completion Rate:</strong> {{ completion_rate|floatformat:1 }}%</li>
        <li><strong>Total Tasks Assigned:</strong> {{ total_tasks }}</li>
        <li><strong>Tasks Completed:</strong> {{ completed_tasks }}</li>
        <li><strong>Required for Approval:</strong> {{ required_tasks }} (33%)</li>
        <li><strong>Still Needed:</strong> {{ missing_tasks }} tasks</li>
    </ul>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0;">
        <h3>⚠️ Action Required</h3>
        <p>To be included in this month's payroll approval, you need to complete <strong>{{ missing_tasks }}</strong> more tasks by the <strong>{{ deadline }}</strong>.</p>
    </div>
    
    <h3>Next Steps:</h3>
    <ol>
        <li>Log into the task management system</li>
        <li>Complete your pending tasks</li>
        <li>Submit evidence for completed tasks</li>
        <li>Ensure you reach the 33% completion threshold</li>
    </ol>
    
    <p>Once you meet the 33% completion requirement, your name will be automatically added to the payroll approval list for next month's submission.</p>
    
    <p>If you have any questions or need assistance, please contact your supervisor or the HR department.</p>
    
    <p>Best regards,<br>
    HR Department<br>
    CODA Analytics</p>
    
    <hr>
    <p style="font-size: 12px; color: #666;">
        This email was sent on {{ current_date }}. 
        Task completion data is updated daily.
    </p>
</body>
</html>
```

### **5. Enhanced UI for Compliance Management**

```html
<!-- finance/templates/finance/approvals/compliance_report.html -->
{% extends 'base.html' %}
{% load static %}

{% block title %}Employee Compliance Report{% endblock %}

{% block content %}
<div class="container-fluid">
    <h2>Employee Compliance Report - 33% Rule</h2>
    <p class="text-muted">Target Month: {{ target_month }}/{{ target_year }}</p>
    
    {% if is_after_15th %}
        <div class="alert alert-warning">
            <strong>Note:</strong> It's after the 15th of the month. 33% compliance rule is now active.
        </div>
    {% else %}
        <div class="alert alert-info">
            <strong>Note:</strong> It's before the 15th of the month. 33% compliance rule is not yet active.
        </div>
    {% endif %}
    
    {% for report in compliance_reports %}
        <div class="card mb-4">
            <div class="card-header">
                <h4>{{ report.department.name }}</h4>
                <span class="badge badge-{% if report.department_compliance_rate >= 80 %}success{% elif report.department_compliance_rate >= 60 %}warning{% else %}danger{% endif %}">
                    {{ report.department_compliance_rate|floatformat:1 }}% Compliant
                </span>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3">
                        <strong>Total Employees:</strong> {{ report.total_employees }}
                    </div>
                    <div class="col-md-3">
                        <strong>Compliant:</strong> {{ report.compliant_employees }}
                    </div>
                    <div class="col-md-3">
                        <strong>Non-Compliant:</strong> {{ report.non_compliant_employees }}
                    </div>
                    <div class="col-md-3">
                        <strong>Rate:</strong> {{ report.department_compliance_rate|floatformat:1 }}%
                    </div>
                </div>
                
                <table class="table table-sm mt-3">
                    <thead>
                        <tr>
                            <th>Employee</th>
                            <th>Completion Rate</th>
                            <th>Tasks Completed</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for data in report.employee_data %}
                            <tr class="{% if data.compliance.is_compliant %}table-success{% else %}table-danger{% endif %}">
                                <td>{{ data.employee.first_name }} {{ data.employee.last_name }}</td>
                                <td>{{ data.compliance.completion_rate|floatformat:1 }}%</td>
                                <td>{{ data.compliance.completed_tasks }}/{{ data.compliance.total_tasks }}</td>
                                <td>
                                    {% if data.compliance.is_compliant %}
                                        <span class="badge badge-success">Compliant</span>
                                    {% else %}
                                        <span class="badge badge-danger">Non-Compliant</span>
                                    {% endif %}
                                </td>
                                <td>
                                    {% if not data.compliance.is_compliant %}
                                        <button class="btn btn-sm btn-warning" onclick="sendReminder('{{ data.employee.id }}')">
                                            Send Reminder
                                        </button>
                                    {% endif %}
                                </td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    {% endfor %}
    
    <div class="mt-4">
        <button class="btn btn-primary" onclick="submitCompliantOnly()">
            Submit Budget with Compliant Employees Only
        </button>
        <button class="btn btn-secondary" onclick="sendNotifications()">
            Send Notifications to Non-Compliant Employees
        </button>
    </div>
</div>

<script>
function submitCompliantOnly() {
    if (confirm('Are you sure you want to submit the budget with only compliant employees? Non-compliant employees will not be included in this month\'s payroll.')) {
        // Submit form with action
        const form = document.createElement('form');
        form.method = 'POST';
        form.innerHTML = '<input type="hidden" name="action" value="submit_compliant_only">';
        form.innerHTML += '{% csrf_token %}';
        document.body.appendChild(form);
        form.submit();
    }
}

function sendNotifications() {
    if (confirm('Send email notifications to all non-compliant employees?')) {
        // Send notifications
        fetch('{% url "finance:send-compliance-notifications" %}', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({action: 'send_notifications'})
        })
        .then(response => response.json())
        .then(data => {
            alert(`Notifications sent to ${data.emails_sent} employees`);
        });
    }
}
</script>
{% endblock %}
```

---

## 🚀 **Implementation Steps**

### **Phase 1: Core Services (Week 1)**
1. **Create EmployeeComplianceService** - Check 33% compliance
2. **Create EnhancedBudgetService** - Integrate compliance with budget submission
3. **Create email templates** - Notify non-compliant employees

### **Phase 2: UI Integration (Week 2)**
1. **Enhance budget approval views** - Add compliance checking
2. **Create compliance report UI** - Show department/employee status
3. **Add notification buttons** - Send reminders to non-compliant employees

### **Phase 3: Testing & Deployment (Week 3)**
1. **Test with sample data** - Verify compliance calculations
2. **Test email notifications** - Ensure proper delivery
3. **Deploy to UAT** - Test with real users

---

## 📊 **Expected Results**

### **Before Implementation:**
- No 33% rule enforcement
- All employees included in payroll regardless of performance
- No accountability for task completion

### **After Implementation:**
- 33% rule enforced at budget submission level
- Non-compliant employees notified via email
- Only compliant employees included in payroll approval
- Clear accountability and performance tracking

---

## 💡 **Additional Features**

### **Future Enhancements:**
1. **Progressive compliance** - Different thresholds for different employee levels
2. **Department targets** - Department-level compliance goals
3. **Historical tracking** - Track compliance trends over time
4. **Automated escalation** - Automatic supervisor notification for repeat non-compliance

**Should I start implementing the EmployeeComplianceService first? This will be the foundation for the entire 33% rule system.**
