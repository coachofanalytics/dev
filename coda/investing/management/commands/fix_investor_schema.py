"""
Management command to add missing columns to investing_investor_information table
Run: python manage.py fix_investor_schema
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Add missing columns to investing_investor_information table'

    def handle(self, *args, **options):
        sql_commands = [
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS contract_submitted_date timestamp with time zone DEFAULT NOW() NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS client_date varchar(100) NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS rep_date varchar(100) NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS contract_signed boolean DEFAULT FALSE NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS contract_signed_date date NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS documents jsonb DEFAULT '[]'::jsonb NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS status varchar(20) DEFAULT 'pending' NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS modification_reason text NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS total_amount numeric(10, 2) NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS investment_threshold integer DEFAULT 10 NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS amount_invested numeric(10, 2) DEFAULT 1000.00 NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS duration integer NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS revenue_share_percentage numeric(5, 2) NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS investment_type varchar(20) DEFAULT 'equity' NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS investment_date date DEFAULT CURRENT_DATE NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS maturity_date date NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS expected_return_rate numeric(5, 2) DEFAULT 8.00 NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS actual_return_rate numeric(5, 2) DEFAULT 0.00 NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS current_value numeric(10, 2) DEFAULT 0.00 NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS total_returns_paid numeric(10, 2) DEFAULT 0.00 NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS investment_purpose text DEFAULT '' NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS quarterly_updates boolean DEFAULT TRUE NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS monthly_reports boolean DEFAULT TRUE NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS model_type varchar(20) DEFAULT 'Installment' NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS beneficiary_name varchar(50) NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS beneficiary_relation varchar(50) NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS contract_date date NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS notes text NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS risk_tolerance varchar(20) DEFAULT 'moderate' NOT NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS kyc_status varchar(20) DEFAULT 'pending' NOT NULL",
            # Foreign key columns (allow NULL initially to avoid constraint violations)
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS investor_id integer NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS last_modified_by_id integer NULL",
            "ALTER TABLE investing_investor_information ADD COLUMN IF NOT EXISTS client_id integer NULL",
        ]

        with connection.cursor() as cursor:
            self.stdout.write(self.style.WARNING('Adding missing columns to investing_investor_information...'))
            
            for i, sql in enumerate(sql_commands, 1):
                try:
                    cursor.execute(sql)
                    column_name = sql.split('ADD COLUMN IF NOT EXISTS')[1].split()[0]
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {i}/{len(sql_commands)}: Added {column_name}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))

            # Verify
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name='investing_investor_information'
            """)
            count = cursor.fetchone()[0]
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ Schema fixed! Table now has {count} columns.'))
            self.stdout.write(self.style.SUCCESS('You can now test /finance/pay/ again.'))

