"""
Management command to list local pg_dump backups.
"""
from django.core.management.base import BaseCommand
from platform_services.database_service import DatabaseService


class Command(BaseCommand):
    help = 'List local pg_dump backups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dir',
            type=str,
            default='/tmp',
            help='Directory to search for backups (default: /tmp)',
        )

    def handle(self, *args, **options):
        backup_dir = options.get('dir')

        self.stdout.write(f'Listing backups in {backup_dir}...\n')
        
        service = DatabaseService()
        result = service.list_local_backups(backup_dir=backup_dir)

        if result.get('success'):
            backups = result.get('backups', [])
            if not backups:
                self.stdout.write(self.style.WARNING('No backups found.'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'Found {len(backups)} backup(s):\n'))
            for backup in backups:
                self.stdout.write(
                    f"  • {backup['filename']}\n"
                    f"    Size: {backup['size_mb']} MB\n"
                    f"    Created: {backup['created_at']}\n"
                    f"    Path: {backup['path']}\n"
                )
        else:
            self.stdout.write(
                self.style.ERROR(f"Failed to list backups: {result.get('error')}")
            )

