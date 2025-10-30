"""
Management command to create PostgreSQL backup and upload to Google Drive.

Automatically maintains only the last 2 backups in Google Drive.
"""
from django.core.management.base import BaseCommand
from platform_services.database_service import DatabaseService
from platform_services.google_drive_service import GoogleDriveBackupService


class Command(BaseCommand):
    help = 'Create PostgreSQL backup and upload to Google Drive (keeps last 2 backups)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep',
            type=int,
            default=2,
            help='Number of backups to keep (default: 2)',
        )
        parser.add_argument(
            '--folder-id',
            type=str,
            help='Google Drive folder ID (defaults to GOOGLE_DRIVE_BACKUP_FOLDER env var)',
        )

    def handle(self, *args, **options):
        keep_count = options.get('keep', 2)
        folder_id = options.get('folder_id')

        self.stdout.write('🚀 Starting backup workflow...\n')

        # Initialize services
        db_service = DatabaseService()
        drive_service = GoogleDriveBackupService(folder_id=folder_id)

        # Run complete backup workflow
        result = drive_service.backup_and_upload(
            database_service=db_service,
            keep_count=keep_count
        )

        # Display results
        if result.get('success'):
            self.stdout.write(self.style.SUCCESS('\n✅ Backup workflow completed successfully!\n'))
            
            if result.get('backup_created'):
                self.stdout.write(f"  📦 Backup created: {result.get('backup_size_mb', 0)} MB")
            
            if result.get('uploaded'):
                self.stdout.write(f"  ☁️  Uploaded to Google Drive")
                self.stdout.write(f"     File ID: {result.get('file_id')}")
                self.stdout.write(f"     Link: {result.get('web_view_link')}")
            
            if result.get('cleanup_done'):
                deleted = result.get('deleted_count', 0)
                if deleted > 0:
                    self.stdout.write(f"  🧹 Cleaned up {deleted} old backup(s)")
                else:
                    self.stdout.write(f"  ✓  No old backups to clean up")
            
            self.stdout.write(f"\n  📊 Keeping last {keep_count} backup(s) in Google Drive")
        else:
            error_msg = result.get('error', 'Unknown error')
            self.stdout.write(self.style.ERROR(f'\n❌ Backup workflow failed: {error_msg}'))
            
            # Show what succeeded
            if result.get('backup_created'):
                self.stdout.write('  ✓ Backup was created locally')
            if result.get('uploaded'):
                self.stdout.write('  ✓ Backup was uploaded to Google Drive')

