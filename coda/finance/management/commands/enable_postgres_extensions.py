"""
Enable PostgreSQL extensions for performance monitoring
Quick Win #1: Database Performance Optimization
"""
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Enable PostgreSQL extensions (pg_stat_statements, pg_trgm) - Quick Win #1'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\n🚀 QUICK WIN #1: Enable PostgreSQL Extensions"))
        self.stdout.write("=" * 70)
        
        extensions = [
            ('pg_stat_statements', 'Query performance tracking - find slow queries!'),
            ('pg_trgm', 'Fuzzy text search (better than LIKE searches)'),
        ]
        
        with connection.cursor() as cursor:
            for ext_name, description in extensions:
                try:
                    self.stdout.write(f"\n🔄 Enabling {ext_name}...")
                    cursor.execute(f"CREATE EXTENSION IF NOT EXISTS {ext_name};")
                    self.stdout.write(self.style.SUCCESS(
                        f"   ✅ {ext_name} enabled!"
                    ))
                    self.stdout.write(f"   📝 {description}")
                except Exception as e:
                    if 'already exists' in str(e).lower():
                        self.stdout.write(self.style.SUCCESS(
                            f"   ✅ {ext_name} already enabled"
                        ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"   ⚠️ Could not enable {ext_name}: {str(e)}"
                        ))
                        self.stdout.write(self.style.WARNING(
                            f"   💡 May require superuser privileges"
                        ))
        
        # Verify extensions
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("🔍 Verifying installed extensions..."))
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT extname, extversion 
                FROM pg_extension 
                WHERE extname IN ('pg_stat_statements', 'pg_trgm')
                ORDER BY extname;
            """)
            results = cursor.fetchall()
            
            if results:
                self.stdout.write(self.style.SUCCESS("\n✅ Successfully Installed:"))
                for name, version in results:
                    self.stdout.write(f"   • {name} (version {version})")
            else:
                self.stdout.write(self.style.WARNING(
                    "\n⚠️ No extensions found. You may need database superuser privileges."
                ))
                self.stdout.write("\n💡 For Heroku, run:")
                self.stdout.write(self.style.WARNING(
                    '   heroku run "cd coda && python manage.py enable_postgres_extensions" --app codatrainingapp'
                ))
        
        # Show immediate value
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("🎯 QUICK WIN UNLOCKED!"))
        self.stdout.write("\n📊 You can now find slow queries instantly!")
        self.stdout.write("\nRun this query to see your slowest operations:")
        self.stdout.write(self.style.WARNING("""
-- Find queries taking > 1 second on average
SELECT 
    substring(query, 1, 100) as query_preview,
    calls,
    ROUND(total_time::numeric / 1000, 2) as total_seconds,
    ROUND(mean_time::numeric / 1000, 2) as avg_seconds,
    ROUND((100 * total_time / sum(total_time) OVER ())::numeric, 2) AS percentage
FROM pg_stat_statements
WHERE mean_time > 1000  -- > 1 second average
ORDER BY mean_time DESC
LIMIT 10;
        """))
        
        self.stdout.write("\n💡 Use pg_trgm for fuzzy search:")
        self.stdout.write(self.style.WARNING("""
-- Instead of slow LIKE queries:
-- SELECT * FROM users WHERE name LIKE '%john%';  -- SLOW!

-- Use fast similarity search:
-- SELECT * FROM users WHERE name % 'john';  -- FAST!
        """))
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("✅ Quick Win #1 Complete!\n"))

