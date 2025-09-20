from professional_services.models import ClientAssessment

def check_client_assesment(user):
    # Define your custom logic here to check if the user has the permission
    # For example, you might check if the user belongs to a specific group or has a certain attribute set.
    client_assesment = ClientAssessment.objects.filter(email=user.email)

    if user.gender == 2:
        return True
    else:
        return (user.is_authenticated and user.category == 1 and client_assesment.exists())  # Job_Applicant category