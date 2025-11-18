import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.prod_settings')

app = Celery('coda_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.beat_schedule = {
    # Monthly task reset - runs on 1st of each month at midnight
    # OPTION 1: Reset on 1st of month
    'monthly_task_reset': {
        'task': 'task_history',  # Maps to dump_data() function
        'schedule': crontab(hour=0, minute=0, day_of_month='1'),  # 1st at 00:00
    },

    # 'login_no_activity_send_sms': {
    #     'task': 'SendMsgApplicatUser',
    #     'schedule': crontab(minute='*'),
    # },

    # 'LBandLSDeduction': {
    #     'task': 'LBandLSDeduction',
    #     'schedule': crontab(minute=0, hour=23, day_of_month='1'),
    # },

    # 'TrainingLoanDeduction': {
    #     'task': 'TrainingLoanDeduction',
    #     'schedule': crontab(minute=0, hour=23, day_of_month='1'),
    # },

    # 'advertisement': {
    #     'task': 'advertisement',
    #     # 'schedule': crontab(minute='*/1'),
    #     'schedule': crontab(0, 0, day_of_month='1'),
    # },

    # 'replies_mails': {
    #     'task': 'replies_job_mail',
    #     # 'schedule': crontab(minute='*/1'),
    #     # 'schedule': crontab(hour=23),
    #     'schedule': crontab(0, 0, day_of_month='1'),
    # },
    # 'auto_upload_evidence': {
    #     'task': 'auto_uplaod_evidence',
    #     # 'schedule': crontab(minute='*/1'),
    #     # 'schedule': crontab(hour=23),
    #     'schedule': crontab(minute=0, hour=1),  # Run at 1:00 AM every day
    # },

}
