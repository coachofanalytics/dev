from finance.models import Payment_History

def check_payment_history_permission(user, pricing_serial):
    # Define your custom logic here to check if the user has the permission
    # For example, you might check if the user belongs to a specific group or has a certain attribute set.

    return (user.is_authenticated and user.is_staff) or (user.is_authenticated and Payment_History.objects.filter(customer=user, pricing_plan = pricing_serial).exists())