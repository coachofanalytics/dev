"""
Management command to list database backups in Google Drive.
"""
from django.core.management.base import BaseCommand
from platform_services.google_drive_service import GoogleDriveBackupService


class Command(BaseCommand):
    help = 'List database backups in Google Drive'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum number of backups to list (default: 10)',
        )
        parser.add_argument(
            '--folder-id',
            type=str,
            help='Google Drive folder ID (defaults to GOOGLE_DRIVE_BACKUP_FOLDER env var)',
        )

    def handle(self, *args, **options):
        limit = options.get('limit', 10)
        folder_id = options.get('folder_id')

        self.stdout.write('📂 Listing backups from Google Drive...\n')

        drive_service = GoogleDriveBackupService(folder_id=folder_id)
        result = drive_service.list_backups(limit=limit)

        if result.get('success'):
            backups = result.get('backups', [])
            
            if not backups:
                self.stdout.write(self.style.WARNING('No backups found in Google Drive.'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'Found {len(backups)} backup(s):\n'))
            
            for i, backup in enumerate(backups, 1):
                self.stdout.write(f"\n  {i}. {backup['filename']}")
                self.stdout.write(f"     Size: {backup['size_mb']} MB ({backup['size']:,} bytes)")
                self.stdout.write(f"     Created: {backup['created_time']}")
                self.stdout.write(f"     File ID: {backup['file_id']}")
                self.stdout.write(f"     Link: {backup['web_view_link']}")
        else:
            self.stdout.write(
                self.style.ERROR(f"Failed to list backups: {result.get('error')}")
            )

