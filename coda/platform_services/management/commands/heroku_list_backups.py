from django.core.management.base import BaseCommand

from platform_services.database_service import DatabaseService


class Command(BaseCommand):
    help = 'List recent Heroku Postgres backups for the given app'

    def add_arguments(self, parser):
        parser.add_argument('--app', type=str, default='codatrainingapp')
        parser.add_argument('--limit', type=int, default=5)

    def handle(self, *args, **options):
        app_name = options['app']
        limit = options['limit']
        service = DatabaseService()
        result = service.list_backups(app_name, limit=limit)
        if not result.get('success'):
            self.stdout.write(self.style.ERROR(
                f"Failed to list backups: {result.get('error')}"
            ))
            return

        backups = result.get('backups', [])
        if not backups:
            self.stdout.write('No backups found')
            return

        for b in backups:
            self.stdout.write(
                f"- id={b.get('id')} status={b.get('status')} size={b.get('size')} created_at={b.get('created_at')}"
            )


