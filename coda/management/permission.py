from accounts.choices import UserCategory as CategoryChoices, ApplicantSubCategoryChoices
from management.services.finance_service_helper import get_finance_task_service

def check_payment_history_permission_student(user):
    # Define your custom logic here to check if the user has the permission
    # For example, you might check if the user belongs to a specific group or has a certain attribute set.
    
    if user.is_authenticated:
        # Use finance service interface instead of direct model import
        finance_service = get_finance_task_service()
        
        # if not finance_service.has_payment_history(user.id) and user.category == CategoryChoices.STUDENT and user.sub_category == StudentSubCategoryChoices.DATA_ANALYTICS:
        #     return  False

        if not finance_service.has_payment_history(user.id) and user.category == CategoryChoices.STUDENT:
            return  False

        return True
    
    return False

def check_payment_history_permission_job_support(user):
    # Define your custom logic here to check if the user has the permission
    # For example, you might check if the user belongs to a specific group or has a certain attribute set.
    if user.is_authenticated:
        # Use finance service interface instead of direct model import
        finance_service = get_finance_task_service()
        
        if not finance_service.has_payment_history(user.id) and user.category == CategoryChoices.CONSULTANT:
            return  False

        return True
    
    return False