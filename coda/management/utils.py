import os
import random
from django.db.models import Sum,Max,Q, F
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from decimal import Decimal, InvalidOperation
import calendar,string
from django.urls import reverse
from urllib.parse import urlencode
from django.utils.text import slugify
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
# from accounts.choices import UserCategory as CategoryChoices
from accounts.choices import UserCategory as CategoryChoices, ApplicantSubCategoryChoices
from importlib import import_module
import logging
logger = logging.getLogger(__name__)

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore

def get_selected_month_year(request, pay_type):
    """
    Determine selected month and year from form or default.
    Always return the selected month, year, and form.
    """
    from .forms import MonthForm

    current_date = datetime.now()
    form = MonthForm()  # Default empty form
    
    if request.method == "POST":
        form = MonthForm(request.POST)
        if form.is_valid():
            return (
                int(form.cleaned_data['month']),
                int(form.cleaned_data['year']),
                form
            )
    
    if pay_type == 'payslip':
        return current_date.month, current_date.year, form
    
    # Default to last month safely
    previous_date = current_date - relativedelta(months=1)
    return previous_date.month, previous_date.year, form


def get_tasks(employee, selected_month, selected_year, pay_type):
    """
    Retrieve tasks based on pay_type and calculate total pay.
    Args:
        employee (Employee): The employee to retrieve tasks for.
        selected_month (int): Selected month for filtering.
        selected_year (int): Selected year for filtering.
        pay_type (str): Title to determine task type ('payslip', 'task_payslip', 'usertasks', 'userhistorytasks', 'tasks', 'historytasks').
    Returns:
        tuple: (QuerySet of tasks, total pay amount, message)
    """
    from .models import Task, TaskHistory

    tasks = None
    message = None
    current_date = datetime.now()

    # Check if selected month and year match the current month and year
    is_current_month = (
        selected_month == current_date.month and selected_year == current_date.year
    )
    if pay_type in ['payslip', 'usertasks', 'tasks']:
        if pay_type == 'tasks':
            # Fetch all tasks for the employee without staff filter
            tasks = Task.objects.filter(employee__is_active=True,employee__is_staff=True)
        else:
            # Fetch tasks for staff employees
            tasks = Task.objects.filter(employee=employee)

    elif pay_type in ['task_payslip', 'usertaskhistory', 'taskhistory']:
        excluded_usernames=["coda_info", "luke", "angel"]
        if pay_type == 'taskhistory':
            # Fetch all TaskHistory records for the employee without staff filter
            tasks = TaskHistory.objects.filter(
                employee__is_active=True,
                employee__is_staff=True,
                daf_date__month=current_date.month,
            ).exclude(
                Q(employee__username__in=excluded_usernames) 
            )
        else:
            # Fetch TaskHistory records for staff employees
            tasks = TaskHistory.objects.filter(
                employee=employee,
                daf_date__month=selected_month,
                daf_date__year=selected_year
            )
    else:
        raise ValueError(
            f"Invalid pay_type: {pay_type}. Expected 'payslip', 'task_payslip', 'usertasks', 'usertaskhistory', 'tasks', 'taskhistory'."
        )
    if tasks is None or not tasks.exists():
        # Custom message if no tasks are found
        message = f"Hi {employee.username}, you do not have history information for {selected_month}/{selected_year}. Kindly contact admin!"

    total_pay = calculate_total_pay(tasks) if tasks and tasks.exists() else 0
    return tasks, total_pay, message


# ================================client assessment==========================
def compute_total_points(instance):
    delta=2
    totalpoints = 0
    try:
        pc=instance.projectcharter-delta
    except:
        pc=0
    try:
        ra=instance.requirementsAnalysis-delta
    except:
        ra=0
    try:
        rpt=instance.reporting-delta
    except:
        rpt=0
    try:
        etl=instance.etl-delta
    except:
        etl=0
    try:
        db=instance.database-delta
    except:
        db=0
    try:
        test=instance.testing-delta
    except:
        test=0
    try:
        dep=instance.deployment-delta
    except:
        dep=0
    try:
        frontend=instance.frontend-delta
    except:
        frontend=0
    try:
        backend=instance.backend-delta
    except:
        backend=0
    
    ############################
    # developer points
    ############################
    #calculation
    #1 days effective hour of work is 6(avg)
    #here 1 sprint = 10 days
    #1 month = 2 sprint
    #we minus 1 year of experiance and only half of it will be counted because half of the year counted as learning
    try:
        developer_point = 0
      
        if instance.it_exp > 0:
            one_year_point = 1440 #24*10*6
            
            it_expiriance = instance.it_exp-1
            developer_point = it_expiriance*one_year_point + (one_year_point/2)

    except:
        pass


    # totalpoints=pc+ra+rpt+etl+db+test+dep+nie+ie+frontend+backend
    totalpoints=pc+ra+rpt+etl+db+test+dep+frontend+backend
    return totalpoints, developer_point


# ================================apis for payslip==========================
def best_employee(task_obj):
    sum_of_tasks = task_obj.annotate(sum=Sum('point'))
    # logger.debug(f'sum_of_tasks: {sum_of_tasks}')
    max_point = sum_of_tasks.aggregate(max=Max('sum')).get('max')
    # logger.debug(f'max_point: {max_point}')
    best_users = tuple(sum_of_tasks.filter(sum=max_point).values_list('employee__username'))
    # logger.debug(f'best_users: {best_users}')
    return best_users

def employee_reward(tasks):
    points = tasks.aggregate(Your_Total_Points=Sum("point"))
    mxpoints = tasks.aggregate(Your_Total_MaxPoints=Sum("mxpoint"))
    try:
        Points = points.get("Your_Total_Points")
    except (TypeError, AttributeError):
        Points = 0
    try:
        MaxPoints = mxpoints.get("Your_Total_MaxPoints")
    except (TypeError, AttributeError):
        MaxPoints = 0
    try:
        point_percentage=round((Points/MaxPoints),2)*100
    except (TypeError, AttributeError):
        point_percentage = 0

    else:
        EOM = Decimal(0.00)  # employee of month
    return point_percentage

# Usint the number of points to assign employees to different groups 
def employee_group_level(historytasks,TaskGroups):                                          
    if historytasks.exists():
        
        count = historytasks.aggregate(total_point=Sum('point'))
        total_point = count.get('total_point')

        if historytasks[0].group == 'Group I':
            
            group_obj = TaskGroups.objects.filter(title='Group I')
            if group_obj.exists():
                group = group_obj.first().id
                group_name = group_obj.first().title
            else:
                group_obj = TaskGroups.objects.create(title='Group I')
                group = group_obj.id
                group_name = group_obj.title

        elif historytasks[0].group == 'Group H':
            
            group_obj = TaskGroups.objects.filter(title='Group H')
            if group_obj.exists():
                group = group_obj.first().id
                group_name = group_obj.first().title
            else:
                group_obj = TaskGroups.objects.create(title='Group H')
                group = group_obj.id
                group_name = group_obj.title

        elif count.get('total_point') < 350:
            group_obj = TaskGroups.objects.filter(title='Group A')
            if group_obj.exists():
                group = group_obj.first().id
                group_name = group_obj.first().title

            else:
                group_obj = TaskGroups.objects.create(title='Group A')
                group = group_obj.id
                group_name = group_obj.title

        elif 350 <= count.get('total_point') and count.get('total_point') < 600:
            group_obj = TaskGroups.objects.filter(title='Group B')
            if group_obj.exists():
                group = group_obj.first().id
                group_name = group_obj.first().title

            else:
                group_obj = TaskGroups.objects.create(title='Group B')
                group = group_obj.id
                group_name = group_obj.title

        elif 600 <= count.get('total_point') and count.get('total_point') < 800:
            group_obj = TaskGroups.objects.filter(title='Group C')
            if group_obj.exists():
                group = group_obj.first().id
                group_name = group_obj.first().title

            else:
                group_obj = TaskGroups.objects.create(title='Group C')
                group = group_obj.id
                group_name = group_obj.title

        elif 800 <= count.get('total_point') and count.get('total_point') < 1000:
            group_obj = TaskGroups.objects.filter(title='Group D')
            if group_obj.exists():
                group = group_obj.first().id
                group_name = group_obj.first().title

            else:
                group_obj = TaskGroups.objects.create(title='Group D')
                group = group_obj.id
                group_name = group_obj.title

        elif 1000 <= count.get('total_point'):
            group_obj = TaskGroups.objects.filter(title='Group E')
            if group_obj.exists():
                group = group_obj.first().id
                group_name = group_obj.first().title

            else:
                group_obj = TaskGroups.objects.create(title='Group E')
                group = group_obj.id
                group_name = group_obj.title

    else:
        total_point = 0
        group_obj = TaskGroups.objects.filter(title='Group A')
        if group_obj.exists():
            group = group_obj.first().id
            group_name = group_obj.first().title

        else:
            group_obj = TaskGroups.objects.create(title='Group A')
            group = group_obj.id   
            group_name = group_obj.title

    
    return group, group_name, total_point

def increment_in_graduation_of_employee(employee, max_earning, new_group, PayslipConfig):
        
    payslipconfig_obj = PayslipConfig.objects.filter(user=employee)

    if payslipconfig_obj.exists():
        
        increment_percentage = payslipconfig_obj.first().web_delta
    
    else:
        payslipconfig_admin_obj = PayslipConfig.objects.filter(user__username='coda_info')
        
        if payslipconfig_admin_obj.exists():
        
            increment_percentage = payslipconfig_admin_obj.first().web_delta
        
        else:

            increment_percentage = 1
    return max_earning + (max_earning*increment_percentage/100)
    
def payinitial(tasks):
    num_tasks = tasks.count()
    Points = tasks.aggregate(Your_Total_Points=Sum("point"))
    Maxpoints = tasks.aggregate(Your_Total_MaxPoints=Sum("mxpoint"))
    Earning = tasks.aggregate(Your_Total_Pay=Sum("mxearning"))
    Maxearning = tasks.aggregate(Your_Total_AssignedAmt=Sum("mxearning"))
    point_percentage = employee_reward(tasks)
    try:
    # current Pay Values
        points = round(Points.get("Your_Total_Points"))
        mxpoints = round(Maxpoints.get("Your_Total_MaxPoints"))
        pay = Earning.get("Your_Total_Pay")
        GoalAmount = Maxearning.get("Your_Total_AssignedAmt")
        pointsbalance = Decimal(mxpoints) - Decimal(points)
    except (TypeError, AttributeError):
        points=0.00
        mxpoints=0.00
        pay=0.00
        GoalAmount=0.00
        pointsbalance=0.00
        pointsbalance=0.00
    return (num_tasks,points,mxpoints,pay,GoalAmount,pointsbalance,point_percentage)

def paymentconfigurations(PayslipConfig, employee):
    try:
        payslip_config = PayslipConfig.objects.get(user=employee)
    except PayslipConfig.DoesNotExist:
        # If the employee does not have a PayslipConfig object, try to use a default one
        try:
            payslip_config = PayslipConfig.objects.latest('id')
        except PayslipConfig.DoesNotExist:
            # If no PayslipConfig objects exist at all, create a default one
            payslip_config = PayslipConfig.objects.create(
                user=employee,
                loan_amount=0.00,
                loan_repayment_percentage=0.00,
                installment_amount=0.00,
                web_pay_hour=0.00,
                web_delta=0.00,
                laptop_status=True,
                loan_status=True
            )

    return payslip_config
  

    # 1st month
    last_day_of_prev_month1 = date.today().replace(day=1) - timedelta(days=1)
    start_day_of_prev_month1 = date.today().replace(day=1) - timedelta(days=last_day_of_prev_month1.day)

    # 2nd month
    last_day_of_prev_month2 = last_day_of_prev_month1.replace(day=1) - timedelta(days=1)
    start_day_of_prev_month2 = last_day_of_prev_month1.replace(day=1) - timedelta(days=last_day_of_prev_month2.day)

    # 3rd month
    last_day_of_prev_month3 = last_day_of_prev_month2.replace(day=1) - timedelta(days=1)
    start_day_of_prev_month3 = last_day_of_prev_month2.replace(day=1) - timedelta(days=last_day_of_prev_month3.day)


def paytime():
    deadline_date = date(
        date.today().year,
        date.today().month,
        calendar.monthrange(date.today().year, date.today().month)[-1],
    )
    # delta = deadline_date - date.today()
    payday = deadline_date + timedelta(days=15)
    delta = relativedelta(deadline_date, date.today())
    # year=delta.years
    # months=delta.months
    time_remaining_days = delta.days
    time_remaining_hours = delta.hours
    time_remaining_minutes = delta.minutes
    today = date(date.today().year, date.today().month, date.today().day)
    year = date.today().year
    month = date.today().month
    day = date.today().day
    target_date= date(
        date.today().year,
        date.today().month,
        calendar.monthrange(date.today().year, date.today().month)[-1],
    )
    # 1st month
    last_day_of_prev_month1 = date.today().replace(day=1) - timedelta(days=1)
    start_day_of_prev_month1 = date.today().replace(day=1) - timedelta(days=last_day_of_prev_month1.day)

    # 2nd month
    last_day_of_prev_month2 = last_day_of_prev_month1.replace(day=1) - timedelta(days=1)
    start_day_of_prev_month2 = last_day_of_prev_month1.replace(day=1) - timedelta(days=last_day_of_prev_month2.day)

    # 3rd month
    last_day_of_prev_month3 = last_day_of_prev_month2.replace(day=1) - timedelta(days=1)
    start_day_of_prev_month3 = last_day_of_prev_month2.replace(day=1) - timedelta(days=last_day_of_prev_month3.day)
    last_month=last_day_of_prev_month1.strftime("%m")
    return (today,year,deadline_date,month,last_month,day,target_date,
            time_remaining_days,time_remaining_hours,time_remaining_minutes,
            payday,start_day_of_prev_month2,last_day_of_prev_month1,last_day_of_prev_month2,
            start_day_of_prev_month3,last_day_of_prev_month3)


def loan_computation(total_pay, user_data, payslip_config):
    """Computes the loan amount, loan payment and loan balance for an employee - Phase 1 simplified approach"""
    if user_data.exists():
        logger.info('Loan exists for this user!')
        # Get the most recent active loan
        active_loan = user_data.filter(status='active').order_by('-id').first()
        
        if active_loan and active_loan.is_outstanding:
            # Use computed balance_amount property
            loan_amount = round(Decimal(active_loan.balance_amount), 2)
            
            # Calculate loan payment based on payslip config
            if payslip_config and hasattr(payslip_config, 'loan_repayment_percentage'):
                loan_payment = round(total_pay * payslip_config.loan_repayment_percentage, 2)
            else:
                # Use default 10% deduction
                loan_payment = active_loan.calculate_monthly_deduction(total_pay, 10.0)
            
            # Ensure payment doesn't exceed loan balance
            if loan_amount < loan_payment:
                loan_payment = loan_amount
            
            # Calculate new balance (computed property will handle this)
            new_balance = loan_amount - Decimal(loan_payment)
            balance_amount = new_balance
            
            logger.info(f'Phase 1 loan computation: amount={loan_amount}, payment={loan_payment}, balance={balance_amount}')
            
            # Record the payment to update the loan
            if loan_payment > 0:
                active_loan.make_payment(loan_payment)
                logger.info(f'Payment of {loan_payment} recorded for loan {active_loan.id}')
            
        else:
            # No active outstanding loan
            loan_amount = Decimal(0)
            loan_payment = Decimal(0)
            new_balance = Decimal(0)
            balance_amount = new_balance
            logger.info('No active outstanding loan found')
            
    else:
        # No loan data - use payslip config defaults
        if payslip_config and hasattr(payslip_config, 'loan_amount'):
            logger.info('Using payslip config loan amount')
            loan_amount = Decimal(payslip_config.loan_amount)
            loan_payment = round(total_pay * payslip_config.loan_repayment_percentage, 2) if hasattr(payslip_config, 'loan_repayment_percentage') else Decimal(0)
            if loan_amount < loan_payment:
                loan_payment = loan_amount
            new_balance = round(Decimal(loan_amount) - Decimal(loan_payment), 2)
            balance_amount = new_balance
        else:
            logger.info('No loan config found')
            loan_amount = Decimal(0)
            loan_payment = round(Decimal(total_pay) * Decimal(0.2), 2)  # Default 20%
            balance_amount = Decimal(0)
            
    return loan_amount, loan_payment, balance_amount


def updateloantable(user_data, employee, total_pay, payslip_config):
    """Update loan table using Phase 1 simplified approach."""
    loan_amount, loan_payment, balance_amount = loan_computation(total_pay, user_data, payslip_config)
    
    if user_data.exists():
        # The loan_computation function now handles payment recording
        # Just log the update
        active_loan = user_data.filter(status='active').order_by('-id').first()
        if active_loan:
            logger.info(f'Updated loan for {employee.username}: balance={active_loan.balance_amount}')
    
    return True


def addloantable(loantable, employee, total_pay, payslip_config, user_data):
    """Add loan table entry using Phase 1 simplified approach."""
    loan_amount, loan_payment, balance_amount = loan_computation(total_pay, user_data, payslip_config)
    
    if user_data.exists():
        # Check if we need to create a new loan record
        active_loan = user_data.filter(status='active').order_by('-id').first()
        if active_loan and active_loan.balance_amount != balance_amount:
            # Create new loan record if balance changed
            try:
                loan_data = loantable(
                    user=employee,
                    category="Debit",
                    amount=loan_amount,
                )
                logger.info(f'New loan record created for {employee.username}')
                return loan_data
            except Exception as e:
                logger.error(f'Error creating loan record: {str(e)}')
                return None
    else:
        # No existing loan - create new one
        try:
            loan_data = loantable(
                user=employee,
                category="Debit",
                amount=loan_amount,
            )
            logger.info(f'New loan record created for {employee.username}')
            return loan_data
        except Exception as e:
            logger.error(f'Error creating loan record: {str(e)}')
            return None

    return None

def lap_save_bonus(payslip_config):
    """Computes the laptop savings, Laptop Bonusloan payment and loan balance for an employee"""
    if payslip_config.laptop_status:
        laptop_saving =Decimal(0.00)
        total_laptop_savings=Decimal(0.00)
        laptop_bonus=payslip_config.lb_amount if payslip_config.user.category==CategoryChoices.APPLICANT and payslip_config.user.sub_category==ApplicantSubCategoryChoices.FULL_TIME else Decimal(0.00)

    else:
        laptop_bonus=Decimal(0.00)
        laptop_saving =Decimal(1000.00)
        total_laptop_savings =Decimal(payslip_config.ls_amount) if payslip_config.ls_amount < 20000 else Decimal(20000.00)

    return laptop_bonus,laptop_saving,total_laptop_savings



def deductions(employee, user_data, payslip_config, total_pay):
    """
    Computes the deductions for an employee, including food, accommodation, maintenance, health, KRA, lap saving, and loan payment.
    """
    # Default deduction values as Decimal
    food_accommodation = Decimal('1000')
    computer_maintenance = Decimal('500')
    health = Decimal('500')
    kra_percentage = Decimal('0.05')
    # lap_saving = Decimal('500')
    loan_payment = Decimal('0')

    if employee.category == CategoryChoices.APPLICANT and employee.sub_category == ApplicantSubCategoryChoices.FULL_TIME:
        if payslip_config:
            # print(employee.category, employee.sub_category)
            food_accommodation = Decimal(payslip_config.food_accommodation)
            computer_maintenance = Decimal(payslip_config.computer_maintenance)
            health = Decimal(payslip_config.health)
            # lap_saving = Decimal(payslip_config.ls_amount) if payslip_config.lp_status else Decimal(0)
            loan_payment = Decimal(loan_computation(total_pay, user_data, payslip_config)[1])
    else:
        # print(employee.category, employee.sub_category)
        food_accommodation = Decimal('0.00')
        computer_maintenance = Decimal('0.00')
        health = Decimal('0.00')
        # lap_saving = Decimal('0.00')

    laptop_bonus,laptop_saving,total_laptop_savings=lap_save_bonus(payslip_config)

    kra = round(Decimal(total_pay) * kra_percentage, 2)
    total_deductions = (
        food_accommodation
        + computer_maintenance
        + health
        + kra
        + laptop_saving
        + loan_payment
    )

    return (
        food_accommodation,
        computer_maintenance,
        health,
        kra,
        laptop_saving,
        total_laptop_savings,
        loan_payment,
        total_deductions,
    )

def bonus(tasks,total_pay,payslip_config):
    """Computes the loan amount, loan payment and loan balance for an employee"""
    # laptop_bonus,laptop_saving=lap_save_bonus(userprofile,payslip_config,employee)
    month=paytime()[3]
    day=paytime()[5]
    (num_tasks,points,mxpoints,pay,GoalAmount,pointsbalance,point_percentage)=payinitial(tasks)
    if payslip_config:
        # -------------points earning-----------
        bonus_points_ammount= points
        if bonus_points_ammount is None:
                bonus_points_ammount = Decimal(0)
                # EOM =payslip_config.eom_bonus   # employee of month
        # -------------Laptop Bonus-----------
        # Lap_Bonus = laptop_bonus #payslip_config.lb_amount
        # -------------holiday earning-----------
        offpay = payslip_config.holiday_pay if month in (12, 1) and day in (24, 25, 26, 31, 1, 2) else Decimal(0.00)
        # -------------late Night earning-----------
        latenight_Bonus =round(total_pay * payslip_config.rp_increment_max_percentage, 2)
        # print("latenight_Bonus====>",latenight_Bonus)
        yearly = round(payslip_config.rp_starting_amount + (total_pay * payslip_config.rp_increment_percentage), 2)
        # -------------Employee of Award(EOM,EOQ,EOY)-----------
        point_percentage=employee_reward(tasks)
        EOM = payslip_config.eom_bonus if point_percentage>=75 else Decimal(0.00)
        EOQ =  Decimal(0.00)
        EOY =  Decimal(0.00)
    else:
        EOM = Decimal(0.00)  # employee of month
        EOQ =  Decimal(0.00)
        EOY =  Decimal(0.00)
        latenight_Bonus =round(total_pay * Decimal(0.05), 2)
        bonus_points_ammount= Decimal(0.00)
        yearly = Decimal(12000)
        offpay = Decimal(0.00)
        # Lap_Bonus =  Decimal(0.00)

    sub_bonus=(Decimal(bonus_points_ammount)+Decimal(latenight_Bonus)+
              +Decimal(EOM)+Decimal(EOQ)+Decimal(EOY)
              +Decimal(offpay))
    return bonus_points_ammount,latenight_Bonus,yearly,offpay,EOM,EOQ,EOY,sub_bonus#,Lap_Bonus


def calculate_total_pay(tasks):
    """
    Calculate total pay from tasks, ensuring Decimal precision.
    Handles invalid pay values gracefully and logs specific error details.
    """
    total_pay = Decimal(0)  # Start with a Decimal

    for task in tasks:
        pay = getattr(task, 'get_pay', 0)  # Safely get the pay attribute with default 0

        try:
            total_pay += Decimal(pay)  # Ensure pay is added as Decimal
        except (ValueError, TypeError, InvalidOperation) as e:
            # Log the error with detailed task information and exact exception
            print(
                f"Error: {e.__class__.__name__} - {str(e)}\n"
                f"Task ID: {getattr(task, 'id', 'N/A')}, Pay Value: {pay}, Task: {task}"
            )
            continue  # Skip invalid tasks and proceed with others

    return total_pay


def get_points_and_earnings(tasks):
    """Calculate points and earnings from tasks."""
    num_tasks = tasks.count()
    points = tasks.aggregate(Your_Total_Points=Sum("point"))
    mxpoints = tasks.aggregate(Your_Total_MaxPoints=Sum("mxpoint"))
    earning = tasks.aggregate(Your_Total_Pay=Sum("mxearning"))
    mxearning = tasks.aggregate(Your_Total_AssignedAmt=Sum("mxearning"))
    pointsbalance = Decimal(mxpoints) - Decimal(points)
    point_percentage = employee_reward(tasks)
    pay = earning.get("Your_Total_Pay")
    GoalAmount = mxearning.get("Your_Total_AssignedAmt")
    return num_tasks,points,mxpoints,pointsbalance, point_percentage, pay, GoalAmount

def get_bonus_and_summary(employee,tasks,total_pay,user_data,payslip_config):
    """Calculate bonus and summary values."""
    bonus_points_ammount, latenight_Bonus, yearly, offpay, EOM, EOQ, EOY, sub_bonus = bonus(tasks, total_pay, payslip_config)
    *_,sub_bonus=bonus(tasks,total_pay,payslip_config)
    # ===============DEDUCTIONS=======================
    total_deduction=deductions(employee,user_data,payslip_config,total_pay)[-1]
    total_bonus = sub_bonus #+ laptop_bonus
    return bonus_points_ammount, latenight_Bonus, yearly, offpay, EOM, EOQ, EOY, sub_bonus, total_deduction, total_bonus

def emp_average_earnings(request,TaskHistory,GoalAmount,employee):
    start_day_of_prev_month2=paytime()[-5]
    last_day_of_prev_month1=paytime()[-4]
    last_day_of_prev_month2=paytime()[-3]
    start_day_of_prev_month3=paytime()[-2]
    # print("last_day_of_prev_month1======>",last_day_of_prev_month1)
    # print("last_day_of_prev_month2======>",last_day_of_prev_month2)
    # print("start_day_of_prev_month3======>",start_day_of_prev_month3)
    last_day_of_prev_month1=paytime()[-3]
    start_day_of_prev_month3=paytime()[-2]
        # print("average_earnings======>",average_earnings)
    history = TaskHistory.objects.filter(
        Q(submission__lte=last_day_of_prev_month1),
        Q(submission__gte=start_day_of_prev_month3),
        Q(employee=employee)
        # Q(employee__username=request.user)
    )
    last3month_history = TaskHistory.objects.filter(
        Q(submission__lte=last_day_of_prev_month1),
        Q(submission__gte=start_day_of_prev_month3),
        Q(employee=employee)
        # Q(employee__username=request.user)
    )
    last2monthhistory = TaskHistory.objects.filter(
        Q(submission__lte=last_day_of_prev_month1),
        Q(submission__gte=start_day_of_prev_month2),
        Q(employee=employee)
        # Q(employee__username=request.user)
    )
    lastmonthhistory = TaskHistory.objects.filter(
        Q(submission__gte=last_day_of_prev_month1),
        Q(employee=employee)
        # Q(employee__username=request.user)
    )

    average_earnings = 0
    counter = 3
    for data in history.all():
        average_earnings += data.get_pay
        # counter = counter+1 
        counter = 3
    average_earnings = round((average_earnings / counter),2)
    if average_earnings == 0:
        average_earnings = GoalAmount
    return average_earnings

# ================================apis for slug==========================
def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    """Generate random string using centralized utility service."""
    try:
        from core.services.utility_service import utility_service
        return utility_service.random_string_generator(size, chars)
    except Exception as e:
        logger.error(f"Error in random_string_generator: {e}")
        # Fallback to original implementation
        return ''.join(random.choice(chars) for _ in range(size))


def unique_slug_generator(instance, new_slug=None):
    """Generate unique slug using centralized utility service."""
    try:
        from core.services.utility_service import utility_service
        return utility_service.generate_unique_slug(instance, new_slug)
    except Exception as e:
        logger.error(f"Error in unique_slug_generator: {e}")
        # Fallback to original implementation
        if new_slug is not None:
            slug = new_slug
        else:
            slug = slugify(instance.title)

        Klass = instance.__class__
        qs_exists = Klass.objects.filter(slug=slug).exists()
        if qs_exists:
            new_slug = "{slug}-{randstr}".format(
                slug=slug,
                randstr=random_string_generator(size=4)
            )
            return unique_slug_generator(instance, new_slug=new_slug)
        return slug

def email_template(subject, to, html_content):
    msg = EmailMultiAlternatives(
        subject, '', settings.EMAIL_HOST_USER, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def split_num_str(my_str):
    num = [x for x in my_str if x.isdigit()]
    num = "".join(num)
    if not num:
        num = None
    return num

def text_num_split(item):
    for index, letter in enumerate(item, 0):
        if letter.isdigit():
            return [item[:index],item[index:]]

def task_assignment_random(employees):
    # departments=[department.name for department in dept_obj ]
    departments=['HR','IT','Finance','Health','Marketing','Basics','IT Projects','Field Projects','Security']
    try:
        departments_per_worker = len(departments) / len(employees)
    except ZeroDivisionError:
        departments_per_worker = len(departments) / 1
    random.shuffle(departments)
    rand_departments = zip(*[iter(departments)] * int(departments_per_worker))
    return employees,rand_departments

def defined_links(request):
    links = {
        'My Meetings': reverse('management:meetings', kwargs={'status': 'company 2'}),
        'My Schedule': reverse('main:my_availability'),
        'My Sessions': reverse('management:user_session', args=[request.user]),
        'My Responses': reverse('professional_services:student_feedback'),
        'Edit Profile': reverse('main:update_profile', args=[request.user.profile.id]),
        'Apply for Loan': reverse('finance:loan-home'),
        # 'Make a Payment': reverse('finance:unified_method_selection'),  # TEMPORARILY DISABLED - URL not available
    }

    # Conditional links based on user category
    if request.user.category == 1:  # Job_Applicant category
        links.update({
            'My Application':reverse('application:policies'),
            'My Interview':reverse('application:interview'),
            'Apply for Internship':reverse('main:contact'),
            'Apply for Training':reverse('main:contact'),
             'Company Policies': reverse('application:policies'),
        })
    elif request.user.is_staff:
        links.update({
            'My DAF': reverse('management:user_pay') + '?' + urlencode({'username': request.user.username, 'pay_type': 'usertasks'}),
            'Last DAF': reverse('management:user_pay') + '?' + urlencode({'username': request.user.username, 'pay_type': 'usertaskhistory'}),
            'My Evidence': reverse('management:user_evidence') + '?' + urlencode({'username': request.user.username}),
            'Evidence': reverse('management:user_evidence'),
            'My Sessions': reverse('management:user_session', args=[request.user]),
            'My Time': reverse('accounts:account-profile', args=[request.user]),
        })
    elif request.user.category in [1, 3, 4, 5, 6, 7]:  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
        if request.user.category == 5:

            links.update({
                'My Time': reverse('accounts:user-list', args=[request.user]),
                'My Contract': reverse('finance:mycontract', args=[request.user]),
                'New Contract': reverse('main:display_service', kwargs={'slug': 'data_analysis'}),
                'Make Payment': reverse('finance:pay'), 
                'Investment Portal': reverse('investing:user_investments', kwargs={'username': request.user.username})
            })
        else:
                links.update({
                'Assessment': reverse('management:clientassessment'),
                'Assignment':reverse('management:assignment_list'),
                'My Training': reverse('professional_services:train'),
                'My Interview': reverse('professional_services:question-detail', kwargs={'question_type': 'resume'}),
                'Job Support': reverse('professional_services:start_training', kwargs={'slug': 'interview'}),
                'My Time': reverse('accounts:user-list', args=[request.user]),
                'My Contract': reverse('finance:mycontract', args=[request.user]),
                'New Contract': reverse('main:display_service', kwargs={'slug': 'data_analysis'}),
                'Make Payment': reverse('finance:pay'),
                
            })

    if request.user.is_superuser:
        # Allow superusers to see all tasks if username is not provided
        links.update({
            'Tasks': reverse('management:user_pay') + '?' + urlencode({
                'username': '',  # Empty username to represent all users
                'pay_type': 'tasks'
            }),
            'History Tasks': reverse('management:user_pay') + '?' + urlencode({
                'username': '',  # Empty username to represent all users
                'pay_type': 'taskhistory'
            }),
        })
    else:
        # Non-superusers can only access their own tasks
        links.update({
            'Tasks': reverse('management:user_pay') + '?' + urlencode({
                'username': request.user.username,
                'pay_type': 'usertasks'
            }),
            'History Tasks': reverse('management:user_pay') + '?' + urlencode({
                'username': request.user.username,
                'pay_type': 'usertaskhistory'
            }),
        })
    return links


def login_user_in_background(email, password):
    # Authenticate the user with provided credentials
    user = authenticate(username=email, password=password)
    
    if user:
        # Create a session manually
        session = SessionStore()
        session.create()  # Initialize session key
        
        # Set session data as Django normally does
        session['_auth_user_id'] = user.id
        session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
        session['_auth_user_hash'] = user.get_session_auth_hash()
        session.save()  # Save the session

        print(f"User {user.email} has been logged in with session ID: {session.session_key}")
        
        # Optionally, save the session key or send it to the user if necessary

    
suggestions = {
    "strong": {
        "description": "You demonstrate a high level of competence in this domain. Here are expert-level strategies to achieve mastery and stay ahead in the field.",
        "recommendations": {
            "project_management": "Lead cross-functional, large-scale initiatives to further hone strategic planning and execution.",
            "requirements_analysis": "Collaborate with senior stakeholders on enterprise-level projects to refine advanced elicitation techniques and solution modeling.",
            "reporting": "Master data storytelling and predictive analytics using cutting-edge tools like Tableau, Power BI, or Looker.",
            "etl": "Delve into real-time data streaming and pipeline optimization with platforms like Apache Kafka or AWS Glue.",
            "database": "Architect high-performance databases and implement advanced indexing, sharding, and partitioning strategies.",
            "testing": "Integrate AI-driven testing frameworks to enhance test automation, coverage, and efficiency.",
            "deployment": "Specialize in advanced continuous integration and delivery pipelines using tools like Spinnaker or ArgoCD.",
            "frontend": "Explore cutting-edge frontend technologies like WebAssembly and advanced state management libraries.",
            "backend": "Architect and implement distributed systems using frameworks like Spring Boot, Django, or Node.js in a microservices ecosystem.",
        }
    },
    "weak": {
        "description": "This area presents opportunities for significant growth. Here are targeted strategies to build a robust foundation and achieve intermediate proficiency.",
        "recommendations": {
            "project_management": "Develop a comprehensive understanding of agile methodologies and pursue advanced certifications like PMI-ACP or PRINCE2.",
            "requirements_analysis": "Enhance skills in creating user stories, workflows, and process diagrams with tools like Lucidchart or Visio.",
            "reporting": "Strengthen fundamentals by integrating data analysis with tools like Google Sheets or Python libraries such as Pandas and Matplotlib.",
            "etl": "Learn foundational and intermediate ETL practices using tools like Talend or Apache Airflow.",
            "database": "Build expertise in relational and non-relational databases, starting with indexing and normalization techniques.",
            "testing": "Expand testing knowledge by exploring unit testing frameworks like PyTest, Mocha, or JUnit.",
            "deployment": "Start by automating basic deployment pipelines and monitoring applications with platforms like Docker and AWS CodePipeline.",
            "frontend": "Progress from core web technologies to interactive applications using frameworks like React or Angular.",
            "backend": "Lay a strong foundation in backend development with RESTful API design and basic authentication mechanisms.",
        }
    }
}
 
import re   
# Optional imports - removed during optimization to reduce slug size
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_AVAILABLE = True
except ImportError:
    Credentials = None
    build = None
    MediaFileUpload = None
    GOOGLE_AVAILABLE = False 
def split_review_by_sections(text):
    # Use regex to split based on numbered sections like "1.", "2.", etc.
    sections = re.split(r'(?=\d+\.)', text)
    # Remove empty strings and strip whitespace from each section
    sections = [section.strip() for section in sections if section.strip()]
    return sections

def upload_file_to_drive(temp_file_path, original_filename, user, task, folder_id):
    """
    Uploads the given file to Google Drive in a specific folder and returns the file's web view link.
    """
    if not GOOGLE_AVAILABLE:
        logger.warning("Google Drive API not available - feature disabled during optimization")
        return None
        
    try:
        creds = Credentials(
            token=os.environ.get('GOOGLE_ACCESS_TOKEN'),
            refresh_token=os.environ.get('GOOGLE_REFRESH_TOKEN'),
            client_id=os.environ.get('GOOGLE_CLIENT_ID'),
            client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
            token_uri="https://oauth2.googleapis.com/token",
            scopes=['https://www.googleapis.com/auth/drive.file']

        )
        service = build('drive', 'v3', credentials=creds)

        # File metadata
        file_metadata = {
            'name': f"{task.id}_{user.username}_{original_filename}",
            'parents': [folder_id]
        }

        # Determine MIME type
        mime_type = 'application/pdf' if original_filename.lower().endswith('.pdf') else 'image/jpeg'  # Adjust as needed

        media = MediaFileUpload(temp_file_path, mimetype=mime_type)

        # Upload the file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        # Set the file to be viewable by anyone with the link
        permission = {
            'type': 'anyone',
            'role': 'reader',
        }
        service.permissions().create(
            fileId=file.get('id'),
            body=permission
        ).execute()

        drive_link = file.get('webViewLink')

        return drive_link

    except Exception as e:
        logger.error(f"Failed to upload file to Google Drive: {e}", exc_info=True)
        return None
    
# def upload_file_to_drive(temp_file_path, original_filename, user, task, parent_folder_id, link_name):
#     """
#     Uploads the given file to Google Drive in a user-specific folder and returns the file's web view link.
#     """
#     try:
#            creds = Credentials(
        #     token=os.environ.get('GOOGLE_ACCESS_TOKEN'),
        #     refresh_token=os.environ.get('GOOGLE_REFRESH_TOKEN'),
        #     client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        #     client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        #     token_uri="https://oauth2.googleapis.com/token",
        #     scopes=['https://www.googleapis.com/auth/drive.file']

        # )
#         service = build('drive', 'v3', credentials=creds)

#         # Check if a folder for the user already exists, or create one
#         user_folder_id = None
#         response = service.files().list(
#             q=f"'{parent_folder_id}' in parents and name='{user.username}' and mimeType='application/vnd.google-apps.folder'",
#             spaces='drive',
#             fields='files(id, name)',
#             pageSize=10
#         ).execute()
#         folders = response.get('files', [])

#         if folders:
#             user_folder_id = folders[0].get('id')
#         else:
#             # Create folder for the user if it doesn't exist
#             folder_metadata = {
#                 'name': user.username,
#                 'mimeType': 'application/vnd.google-apps.folder',
#                 'parents': [parent_folder_id]
#             }
#             user_folder = service.files().create(
#                 body=folder_metadata,
#                 fields='id'
#             ).execute()
#             user_folder_id = user_folder.get('id')

#         # Format the filename with date and link name
#         current_date = datetime.now().strftime("%Y-%m-%d")
#         formatted_filename = f"{current_date}_{link_name}_{original_filename}"

#         # Prepare file metadata
#         file_metadata = {
#             'name': formatted_filename,
#             'parents': [user_folder_id]
#         }

#         # Set MIME type based on file extension
#         mime_type = 'application/pdf' if original_filename.lower().endswith('.pdf') else 'image/jpeg'
#         media = MediaFileUpload(temp_file_path, mimetype=mime_type)

#         # Upload the file
#         file = service.files().create(
#             body=file_metadata,
#             media_body=media,
#             fields='id, webViewLink'
#         ).execute()

#         # Set the file permissions to be viewable by anyone with the link
#         permission = {
#             'type': 'anyone',
#             'role': 'reader',
#         }
#         service.permissions().create(
#             fileId=file.get('id'),
#             body=permission
#         ).execute()

#         drive_link = file.get('webViewLink')
#         return drive_link

#     except Exception as e:
#         logger.error(f"Failed to upload file to Google Drive: {e}", exc_info=True)
#         return None


# def update_payslipfields(tasks, PayConfig):
#     """
#     Increase `ls_amount` for active employees and update `rp_starting_amount`
#     based on tenure and total pay from tasks.
#     """
#     try:
#         # Get the current year for filtering tasks
#         current_year = timezone.now().year
        
#         # Step 1: Filter staff on payroll
#         staff_on_payroll = PayConfig.filter(user__is_staff=True)
        
#         # Step 2: Update ls_amount for eligible users
#         updated_count = PayConfig.filter(
#             user__is_staff=True,
#             laptop_status=False,
#             ls_amount__lt=Decimal(20000.00)
#         ).update(ls_amount=F('ls_amount') + Decimal(1000.00))
        
#         # Step 3: Update Retirement Amount Based on Tenure and Pay
#         retirement_updated_count = 0
        
#         for config in staff_on_payroll:
#             # Get Employee Tenure (in months)
#             tenure = getattr(config.user, 'tenure', 0)  # Fallback to 0 if tenure is not set
            
#             # Fetch Tasks for the Current Year
#             employee_tasks = tasks.filter(
#                 employee=config.user,
#                 submission__icontains=current_year
#             )
            
#             total_pay = calculate_total_pay(employee_tasks)
            
#             # Calculate Retirement Increment Based on Tenure
#             if tenure > 36:
#                 increment_percentage = Decimal(0.05)  # 5% for > 36 months
#             else:
#                 # Scale increment percentage between 1% and 5%
#                 increment_percentage = Decimal(0.01) + (Decimal(0.04) * (tenure / 36))
            
#             # Calculate Increment
#             retirement_increment = total_pay * increment_percentage
#             Decimal(config.rp_starting_amount) += retirement_increment
            
#             # Save the updated config
#             config.save()
#             retirement_updated_count += 1
        
#         # Step 4: Prepare the Message
#         message = (
#             f"We are done transferring your tasks to history and resetting the points to zero. "
#             f"Furthermore, {updated_count} active user(s) had their ls_amount increased by 1000 for laptop savings, "
#             f"and {retirement_updated_count} user(s) had their rp_starting_amount updated based on tenure and pay."
#         )
        
#         return {'status': 'success', 'message': message}
    
#     except Exception as e:
#         message = f"An error occurred while updating ls_amount or rp_starting_amount: {e}"
#         return {'status': 'error', 'message': message}
    