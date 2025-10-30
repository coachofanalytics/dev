"""
Management command to cleanup old backups in Google Drive.
"""
from django.core.management.base import BaseCommand
from platform_services.google_drive_service import GoogleDriveBackupService


class Command(BaseCommand):
    help = 'Cleanup old backups in Google Drive (keeps most recent N backups)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep',
            type=int,
            default=2,
            help='Number of most recent backups to keep (default: 2)',
        )
        parser.add_argument(
            '--folder-id',
            type=str,
            help='Google Drive folder ID (defaults to GOOGLE_DRIVE_BACKUP_FOLDER env var)',
        )

    def handle(self, *args, **options):
        keep_count = options.get('keep', 2)
        folder_id = options.get('folder_id')

        self.stdout.write(f'🧹 Cleaning up old backups (keeping last {keep_count})...\n')

        drive_service = GoogleDriveBackupService(folder_id=folder_id)
        result = drive_service.cleanup_old_backups(keep_count=keep_count)

        if result.get('success'):
            deleted_count = result.get('deleted_count', 0)
            
            if deleted_count == 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ {result.get('message', 'No backups to delete.')}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✅ Deleted {deleted_count} old backup(s):\n"
                    )
                )
                for deleted in result.get('deleted_files', []):
                    self.stdout.write(f"  • {deleted['filename']} (ID: {deleted['file_id']})")
                
                self.stdout.write(f"\n  📊 Kept {keep_count} most recent backup(s)")
        else:
            self.stdout.write(
                self.style.ERROR(f"Failed to cleanup backups: {result.get('error')}")
            )

