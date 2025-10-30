"""
Management command to create PostgreSQL backups using pg_dump.

Works with any PostgreSQL database (RDS, Heroku Postgres, local, etc.)
"""
from django.core.management.base import BaseCommand
from platform_services.database_service import DatabaseService


class Command(BaseCommand):
    help = 'Create a PostgreSQL backup using pg_dump'

    def add_arguments(self, parser):
        parser.add_argument(
            '--database-url',
            type=str,
            help='Database URL (defaults to DATABASE_URL env var)',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output path (defaults to /tmp/backup_<timestamp>.sql)',
        )

    def handle(self, *args, **options):
        database_url = options.get('database_url')
        output_path = options.get('output')

        self.stdout.write('Creating PostgreSQL backup using pg_dump...')
        
        service = DatabaseService()
        result = service.create_pg_dump_backup(
            database_url=database_url,
            output_path=output_path,
        )

        if result.get('success'):
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Backup created successfully:\n"
                    f"   Path: {result['backup_path']}\n"
                    f"   Size: {result['size_mb']} MB ({result['size_bytes']:,} bytes)"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ Backup failed: {result.get('error')}")
            )

