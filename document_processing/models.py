# from django.db import models

# # Create your models here.

# class DocumentDraft(models.Model):
#     application = models.OneToOneField('DocumentApplication', on_delete=models.CASCADE)
#     completion_percentage = models.IntegerField(default=0)
#     draft_data = models.JSONField(blank=True, null=True)

#     def __str__(self):
#         return f"Draft for {self.application}"
# from this create for me all the functional base using def