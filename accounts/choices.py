from django.db import models

class CategoryChoices(models.IntegerChoices):
    Job_Applicant = 1
    Coda_Staff_Member = 2
    Jobsupport = 3
    Student = 4
    investor = 5
    Vendor=6
    General_User = 7

    
class SubCategoryChoices(models.IntegerChoices):
    No_selection = 0
    Full_time = 1
    Contractual = 2
    Agent = 3
    Short_Term = 4
    Long_Term = 5
    Other = 6


# class GenderChoices(models.IntegerChoices):
#     Male = 1
#     Female = 2