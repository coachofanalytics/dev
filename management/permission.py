from accounts.choices import UserCategory as CategoryChoices, ApplicantSubCategoryChoices
from finance.models import Payment_History

def check_payment_history_permission_student(user):
    # Define your custom logic here to check if the user has the permission
    # For example, you might check if the user belongs to a specific group or has a certain attribute set.
    
    if user.is_authenticated:
        # if not Payment_History.objects.filter(customer=user).exists() and user.category == CategoryChoices.STUDENT and user.sub_category == StudentSubCategoryChoices.DATA_ANALYTICS:
        #     return  False

        if not Payment_History.objects.filter(customer=user).exists() and user.category == CategoryChoices.STUDENT:
            return  False

        return True
    
    return False

def check_payment_history_permission_job_support(user):
    # Define your custom logic here to check if the user has the permission
    # For example, you might check if the user belongs to a specific group or has a certain attribute set.
    if user.is_authenticated:
        
        if not Payment_History.objects.filter(customer=user).exists() and user.category == CategoryChoices.CONSULTANT:
            return  False

        return True
    
    return False