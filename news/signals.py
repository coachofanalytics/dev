from django.dispatch import receiver
from .models import NewsArticle, Subscriber
from django.db.models.signals import post_save


@receiver(post_save, sender=NewsArticle)
def  send_news_blast(sender, instance, created, **kwargs):
    if instance.status == 'PUBLISHED':
        subscribers = Subscriber.objects.filter(confirmed = True).values_list('email', flat=True)

        if subscribers:
            subject = f"Breaking News: {instance.title}"
            message = f"Check out our latest update: \n\n{instance.ai_summary}\n\nRead more at: http://127.0.0.1:8000/news/"
            from_email = 'dc48knews@coda.dev'

            try:
                send_mail = (subject, message, from_email, list(subscribers))
                print(f"success: News blast sent to {len(subscribers)} verified readers.")
            except Exception as e:
                print(f"Email Error: {e}")

