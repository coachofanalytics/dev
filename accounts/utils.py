from datetime import date
import string
import secrets

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + "!@#$%&"
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password

def agreement_data(request):
    contract_data = {}
    contract_data["first_name"] = request.POST.get("first_name")
    contract_data["last_name"] = request.POST.get("last_name")
    contract_data["address"] = request.POST.get("address")
    contract_data["category"] = request.POST.get("category")
    contract_data["sub_category"] = request.POST.get("sub_category")
    contract_data["username"] = request.POST.get("username")
    contract_data["password1"] = request.POST.get("password1")
    contract_data["password2"] = request.POST.get("password2")
    contract_data["email"] = request.POST.get("email")
    contract_data["phone"] = request.POST.get("phone")
    contract_data["gender"] = request.POST.get("gender")
    contract_data["city"] = request.POST.get("city")
    contract_data["state"] = request.POST.get("state")
    contract_data["country"] = request.POST.get("country")
    contract_data["resume_file"] = request.POST.get("resume_file")
    today = date.today()
    contract_date = today.strftime("%d %B, %Y")
    return contract_data,contract_date

def compute_default_fee(category, default_amounts, Default_Payment_Fees):
    if default_amounts:
        default_fee = default_amounts.first()
    else:
        default_fee = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=1000,
            job_plan_hours_per_month=40,
            student_down_payment_per_month=500,
            student_bonus_payment_per_month=100,
            )
    return default_fee


JOB_SUPPORT_CATEGORIES = [
    "Job_Support", "job_support", "jobsupport", "Jobsupport", 
    "JobSupport", "Job Support", "Job support", "job support"

]



def employees():
    active_employees = CustomerUser.objects.filter(
                                             Q(is_staff=True),Q(is_active=True)
                                          ).order_by("-date_joined")
    
    # former_employees = CustomerUser.objects.filter(
    #                                          Q(is_staff=True),Q(is_active=True),Q(sub_category=5)
    #                                       ).order_by("-date_joined")
    
    employees_categories_list = CustomerUser.objects.values_list(
                    'sub_category', flat=True).distinct()
    
    
    # employees_categories = [subcat for subcat in employees_categories_list if subcat in (1,2,3)]
    # employees_categories = [subcat for subcat in employees_categories_list]
    employees_categories = [subcat for subcat in employees_categories_list if subcat in (0,1,2,3,4,5,6)]
    employee_subcategories=list(set(employees_categories))
    return (employee_subcategories,active_employees)