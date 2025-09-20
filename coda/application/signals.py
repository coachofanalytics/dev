from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Trainee_Assessment
from management.models import TaskLinks ,Task

@receiver(post_save, sender=Trainee_Assessment)
def create_tasklink_instance(sender, instance, created, **kwargs):
    activity_instance=Task.objects.filter(activity_name='Training Assessment').first()
    if created and not TaskLinks.objects.filter(added_by=instance.assessor,link=instance.uploadlinkurl).exists():
        TaskLinks.objects.create(
            task = activity_instance,
            added_by = instance.assessor,
            link_name = "Training Assessment",
            description = f"Training Assessment for {instance.trainee_username}",
            link=instance.uploadlinkurl,
        )