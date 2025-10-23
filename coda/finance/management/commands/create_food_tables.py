"""
Management command to create food management tables

Use this when migration fails due to existing tables
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Create food management tables if they don\'t exist'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write('Creating food management tables...')
            
            # Check and create tables one by one
            tables_to_create = {
                'finance_foodpricehistory': '''
                    CREATE TABLE IF NOT EXISTS finance_foodpricehistory (
                        id BIGSERIAL PRIMARY KEY,
                        food_id BIGINT NOT NULL REFERENCES finance_food(id) ON DELETE CASCADE,
                        old_price NUMERIC(10, 2),
                        new_price NUMERIC(10, 2) NOT NULL,
                        change_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        change_percentage NUMERIC(5, 2),
                        supplier_id BIGINT REFERENCES finance_supplier(id) ON DELETE SET NULL,
                        changed_by_id BIGINT REFERENCES accounts_customeruser(id) ON DELETE SET NULL,
                        change_reason TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    CREATE INDEX IF NOT EXISTS finance_foodpricehistory_food_id_idx ON finance_foodpricehistory(food_id);
                    CREATE INDEX IF NOT EXISTS finance_foodpricehistory_change_date_idx ON finance_foodpricehistory(change_date);
                ''',
                
                'finance_foodinventory': '''
                    CREATE TABLE IF NOT EXISTS finance_foodinventory (
                        id BIGSERIAL PRIMARY KEY,
                        food_item_id BIGINT NOT NULL REFERENCES finance_food(id) ON DELETE CASCADE,
                        location_id BIGINT NOT NULL,
                        quantity NUMERIC(10, 2) NOT NULL DEFAULT 0,
                        reorder_level NUMERIC(10, 2) NOT NULL DEFAULT 10,
                        reorder_quantity NUMERIC(10, 2) NOT NULL DEFAULT 50,
                        status VARCHAR(20) NOT NULL DEFAULT 'in_stock',
                        daily_consumption_rate NUMERIC(10, 2),
                        last_restocked_date TIMESTAMP WITH TIME ZONE,
                        last_restocked_quantity NUMERIC(10, 2),
                        last_updated_by_id BIGINT REFERENCES accounts_customeruser(id) ON DELETE SET NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        UNIQUE(food_item_id, location_id)
                    );
                    CREATE INDEX IF NOT EXISTS finance_foodinventory_food_item_id_idx ON finance_foodinventory(food_item_id);
                    CREATE INDEX IF NOT EXISTS finance_foodinventory_location_id_idx ON finance_foodinventory(location_id);
                    CREATE INDEX IF NOT EXISTS finance_foodinventory_status_idx ON finance_foodinventory(status);
                ''',
                
                'finance_foodpurchasetransaction': '''
                    CREATE TABLE IF NOT EXISTS finance_foodpurchasetransaction (
                        id BIGSERIAL PRIMARY KEY,
                        food_item_id BIGINT NOT NULL REFERENCES finance_food(id) ON DELETE CASCADE,
                        inventory_id BIGINT REFERENCES finance_foodinventory(id) ON DELETE SET NULL,
                        quantity NUMERIC(10, 2) NOT NULL,
                        unit_price NUMERIC(10, 2) NOT NULL,
                        total_amount NUMERIC(15, 2) NOT NULL,
                        currency VARCHAR(3) NOT NULL DEFAULT 'KES',
                        purchase_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        payment_method VARCHAR(25) NOT NULL DEFAULT 'Mpesa',
                        receipt_number VARCHAR(100),
                        supplier_id BIGINT REFERENCES finance_supplier(id) ON DELETE SET NULL,
                        purchased_by_id BIGINT REFERENCES accounts_customeruser(id) ON DELETE SET NULL,
                        transaction_id BIGINT UNIQUE REFERENCES finance_transaction(id) ON DELETE SET NULL,
                        notes TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    CREATE INDEX IF NOT EXISTS finance_foodpurchasetransaction_food_item_id_idx ON finance_foodpurchasetransaction(food_item_id);
                    CREATE INDEX IF NOT EXISTS finance_foodpurchasetransaction_inventory_id_idx ON finance_foodpurchasetransaction(inventory_id);
                    CREATE INDEX IF NOT EXISTS finance_foodpurchasetransaction_purchase_date_idx ON finance_foodpurchasetransaction(purchase_date);
                ''',
                
                'finance_foodconsumptionlog': '''
                    CREATE TABLE IF NOT EXISTS finance_foodconsumptionlog (
                        id BIGSERIAL PRIMARY KEY,
                        inventory_id BIGINT NOT NULL REFERENCES finance_foodinventory(id) ON DELETE CASCADE,
                        quantity_consumed NUMERIC(10, 2) NOT NULL,
                        consumption_date DATE NOT NULL DEFAULT CURRENT_DATE,
                        consumption_type VARCHAR(20) NOT NULL DEFAULT 'normal',
                        recorded_by_id BIGINT REFERENCES accounts_customeruser(id) ON DELETE SET NULL,
                        notes TEXT,
                        is_automatic BOOLEAN NOT NULL DEFAULT FALSE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    CREATE INDEX IF NOT EXISTS finance_foodconsumptionlog_inventory_id_idx ON finance_foodconsumptionlog(inventory_id);
                    CREATE INDEX IF NOT EXISTS finance_foodconsumptionlog_consumption_date_idx ON finance_foodconsumptionlog(consumption_date);
                    CREATE INDEX IF NOT EXISTS finance_foodconsumptionlog_consumption_type_idx ON finance_foodconsumptionlog(consumption_type);
                ''',
                
                'finance_foodrestockrequest': '''
                    CREATE TABLE IF NOT EXISTS finance_foodrestockrequest (
                        id BIGSERIAL PRIMARY KEY,
                        inventory_id BIGINT NOT NULL REFERENCES finance_foodinventory(id) ON DELETE CASCADE,
                        requested_quantity NUMERIC(10, 2) NOT NULL,
                        estimated_cost NUMERIC(12, 2) NOT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'pending',
                        requested_by_id BIGINT REFERENCES accounts_customeruser(id) ON DELETE SET NULL,
                        approved_by_id BIGINT REFERENCES accounts_customeruser(id) ON DELETE SET NULL,
                        approved_at TIMESTAMP WITH TIME ZONE,
                        rejection_reason TEXT,
                        budget_request_id BIGINT UNIQUE REFERENCES finance_budgetrequest(id) ON DELETE SET NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    CREATE INDEX IF NOT EXISTS finance_foodrestockrequest_inventory_id_idx ON finance_foodrestockrequest(inventory_id);
                    CREATE INDEX IF NOT EXISTS finance_foodrestockrequest_status_idx ON finance_foodrestockrequest(status);
                    CREATE INDEX IF NOT EXISTS finance_foodrestockrequest_created_at_idx ON finance_foodrestockrequest(created_at);
                ''',
            }
            
            for table_name, sql in tables_to_create.items():
                try:
                    cursor.execute(sql)
                    self.stdout.write(self.style.SUCCESS(f'✅ Created/verified {table_name}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Error with {table_name}: {e}'))
            
            self.stdout.write(self.style.SUCCESS('\n🎉 Food management tables created successfully!'))
            self.stdout.write('\nNext steps:')
            self.stdout.write('1. Test the dashboard: http://localhost:8080/finance/food/dashboard/')
            self.stdout.write('2. Create test data in Django admin')
            self.stdout.write('3. Try logging consumption and purchases')

