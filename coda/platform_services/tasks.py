import logging
from celery import shared_task

from .database_service import DatabaseService


logger = logging.getLogger(__name__)


@shared_task(name='platform_services.daily_backup')
def daily_backup_task(app_name: str = 'codatrainingapp'):
    """Create a daily backup for the given Heroku app.

    Minimal task – return dict payload and never raise.
    """
    service = DatabaseService()
    result = service.create_backup(app_name)
    if result.get('success'):
        logger.info('Daily backup created: %s', result.get('backup_id'))
    else:
        logger.error('Daily backup failed: %s', result.get('error'))
    return result


