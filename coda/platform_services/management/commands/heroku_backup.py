from django.core.management.base import BaseCommand

from platform_services.database_service import DatabaseService


class Command(BaseCommand):
    help = 'Create a Heroku Postgres backup for the given app'

    def add_arguments(self, parser):
        parser.add_argument('--app', type=str, default='codatrainingapp')

    def handle(self, *args, **options):
        app_name = options['app']
        service = DatabaseService()
        result = service.create_backup(app_name)
        if result.get('success'):
            self.stdout.write(self.style.SUCCESS(
                f"Backup created: {result.get('backup_id')}"
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"Backup failed: {result.get('error')}"
            ))


