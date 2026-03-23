from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.core.mail import send_mail  
from .models import NewsArticle, Subscriber


@receiver(pre_save, sender=NewsArticle)
def track_previous_status(sender, instance, **kwargs):
   
    if instance.pk:
        try:
            old = NewsArticle.objects.get(pk=instance.pk)
            instance._previous_status = old.status
        except NewsArticle.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=NewsArticle)
def send_news_blast(sender, instance, created, **kwargs):
    previous = getattr(instance, '_previous_status', None)

   
    if instance.status == 'PUBLISHED' and previous != 'PUBLISHED':
        subscribers = Subscriber.objects.filter(
            confirmed=True,
            is_active=True
        ).values_list('email', flat=True)

        if subscribers:
            subject = f"Breaking News: {instance.title}"
            message = (
                f"Check out our latest update:\n\n"
                f"{instance.ai_summary}\n\n"
                f"Read more at: https://codadev.herokuapp.com/news/"
            )
            from_email = 'dc48knews@coda.dev'

            try:
                send_mail(subject, message, from_email, list(subscribers))
                print(f"Success: News blast sent to {len(subscribers)} verified readers.")
            except Exception as e:
                print(f"Email Error: {e}")