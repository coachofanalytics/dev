"""
Create Managed Trading Tables

Management command to create the new managed trading database tables manually.
This bypasses the migration system for safety on production database.
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Create managed trading tables in database'
    
    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write('Creating managed trading tables...')
            
            # Create ManagedTradingAccount table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS investing_managedtradingaccount (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP WITH TIME ZONE,
                    updated_at TIMESTAMP WITH TIME ZONE,
                    is_active BOOLEAN DEFAULT FALSE,
                    is_featured BOOLEAN DEFAULT FALSE,
                    client_id INTEGER NOT NULL REFERENCES accounts_customeruser(id) ON DELETE RESTRICT,
                    account_number VARCHAR(20) UNIQUE NOT NULL,
                    account_name VARCHAR(100) NOT NULL,
                    account_manager_id INTEGER REFERENCES accounts_customeruser(id) ON DELETE SET NULL,
                    initial_capital NUMERIC(12, 2) NOT NULL,
                    current_balance NUMERIC(12, 2) NOT NULL,
                    cash_available NUMERIC(12, 2) NOT NULL,
                    cash_reserved NUMERIC(12, 2) DEFAULT 0.00,
                    high_water_mark NUMERIC(12, 2) NOT NULL,
                    fee_tier VARCHAR(20) DEFAULT 'professional',
                    management_fee_percentage NUMERIC(5, 2) DEFAULT 1.50,
                    performance_fee_percentage NUMERIC(5, 2) DEFAULT 20.00,
                    performance_threshold NUMERIC(5, 2) DEFAULT 8.00,
                    session_fee NUMERIC(6, 2) DEFAULT 50.00,
                    sessions_per_month INTEGER DEFAULT 8,
                    monthly_platform_fee NUMERIC(6, 2) DEFAULT 20.00,
                    sessions_completed_this_month INTEGER DEFAULT 0,
                    total_sessions_completed INTEGER DEFAULT 0,
                    next_session_date TIMESTAMP WITH TIME ZONE,
                    max_position_risk NUMERIC(12, 2) DEFAULT 7000.00,
                    max_total_risk NUMERIC(5, 2) DEFAULT 15.00,
                    max_daily_loss NUMERIC(5, 2) DEFAULT 2.00,
                    max_weekly_loss NUMERIC(5, 2) DEFAULT 5.00,
                    max_monthly_loss NUMERIC(5, 2) DEFAULT 10.00,
                    max_positions INTEGER DEFAULT 10,
                    status VARCHAR(20) DEFAULT 'pending',
                    trading_enabled BOOLEAN DEFAULT TRUE,
                    auto_trading_enabled BOOLEAN DEFAULT FALSE,
                    activation_date DATE,
                    closure_date DATE,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    losing_trades INTEGER DEFAULT 0,
                    total_profit_loss NUMERIC(12, 2) DEFAULT 0.00,
                    total_fees_paid NUMERIC(12, 2) DEFAULT 0.00,
                    last_fee_calculation_date DATE
                );
            """)
            self.stdout.write(self.style.SUCCESS('✓ Created ManagedTradingAccount table'))
            
            # Create indexes for ManagedTradingAccount
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_managed_account_client_status 
                ON investing_managedtradingaccount(client_id, status);
                
                CREATE INDEX IF NOT EXISTS idx_managed_account_number 
                ON investing_managedtradingaccount(account_number);
                
                CREATE INDEX IF NOT EXISTS idx_managed_account_manager_status 
                ON investing_managedtradingaccount(account_manager_id, status);
            """)
            
            # Create OptionsPosition table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS investing_optionsposition (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP WITH TIME ZONE,
                    updated_at TIMESTAMP WITH TIME ZONE,
                    is_active BOOLEAN DEFAULT FALSE,
                    is_featured BOOLEAN DEFAULT FALSE,
                    managed_account_id INTEGER NOT NULL REFERENCES investing_managedtradingaccount(id) ON DELETE CASCADE,
                    symbol VARCHAR(10) NOT NULL,
                    strategy VARCHAR(20) NOT NULL,
                    positions JSONB NOT NULL,
                    capital_required NUMERIC(12, 2) NOT NULL,
                    premium_collected NUMERIC(10, 2) NOT NULL,
                    max_profit NUMERIC(10, 2) NOT NULL,
                    max_loss NUMERIC(12, 2) NOT NULL,
                    position_delta NUMERIC(8, 4) DEFAULT 0.0000,
                    position_theta NUMERIC(8, 4) DEFAULT 0.0000,
                    position_gamma NUMERIC(8, 4) DEFAULT 0.0000,
                    position_vega NUMERIC(8, 4) DEFAULT 0.0000,
                    entry_date DATE NOT NULL,
                    expiration_date DATE NOT NULL,
                    exit_date DATE,
                    status VARCHAR(20) DEFAULT 'open',
                    current_value NUMERIC(10, 2) DEFAULT 0.00,
                    realized_pnl NUMERIC(10, 2) DEFAULT 0.00,
                    unrealized_pnl NUMERIC(10, 2) DEFAULT 0.00,
                    exit_reason VARCHAR(20),
                    exit_price NUMERIC(10, 2),
                    notes TEXT
                );
            """)
            self.stdout.write(self.style.SUCCESS('✓ Created OptionsPosition table'))
            
            # Create indexes for OptionsPosition
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_position_account_status 
                ON investing_optionsposition(managed_account_id, status);
                
                CREATE INDEX IF NOT EXISTS idx_position_symbol_status 
                ON investing_optionsposition(symbol, status);
                
                CREATE INDEX IF NOT EXISTS idx_position_expiration_status 
                ON investing_optionsposition(expiration_date, status);
            """)
            
            # Create TradingRule table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS investing_tradingrule (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP WITH TIME ZONE,
                    updated_at TIMESTAMP WITH TIME ZONE,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_featured BOOLEAN DEFAULT FALSE,
                    managed_account_id INTEGER NOT NULL REFERENCES investing_managedtradingaccount(id) ON DELETE CASCADE,
                    rule_name VARCHAR(100) NOT NULL,
                    rule_type VARCHAR(20) NOT NULL,
                    rule_config JSONB NOT NULL,
                    priority INTEGER DEFAULT 10
                );
            """)
            self.stdout.write(self.style.SUCCESS('✓ Created TradingRule table'))
            
            # Create TradingActivity table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS investing_tradingactivity (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP WITH TIME ZONE,
                    updated_at TIMESTAMP WITH TIME ZONE,
                    is_active BOOLEAN DEFAULT FALSE,
                    is_featured BOOLEAN DEFAULT FALSE,
                    managed_account_id INTEGER NOT NULL REFERENCES investing_managedtradingaccount(id) ON DELETE CASCADE,
                    position_id INTEGER REFERENCES investing_optionsposition(id) ON DELETE SET NULL,
                    activity_type VARCHAR(30) NOT NULL,
                    description TEXT NOT NULL,
                    data_snapshot JSONB DEFAULT '{}',
                    performed_by_id INTEGER REFERENCES accounts_customeruser(id) ON DELETE SET NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                );
            """)
            self.stdout.write(self.style.SUCCESS('✓ Created TradingActivity table'))
            
            # Create TradingSession table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS investing_tradingsession (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP WITH TIME ZONE,
                    updated_at TIMESTAMP WITH TIME ZONE,
                    is_active BOOLEAN DEFAULT FALSE,
                    is_featured BOOLEAN DEFAULT FALSE,
                    managed_account_id INTEGER NOT NULL REFERENCES investing_managedtradingaccount(id) ON DELETE CASCADE,
                    session_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    session_duration_minutes INTEGER DEFAULT 30,
                    session_type VARCHAR(20) NOT NULL,
                    topics_discussed TEXT NOT NULL,
                    action_items JSONB DEFAULT '[]',
                    session_notes TEXT,
                    client_feedback TEXT,
                    fee_charged NUMERIC(6, 2) DEFAULT 50.00,
                    is_billed BOOLEAN DEFAULT FALSE,
                    billing_date DATE,
                    recording_url VARCHAR(200)
                );
            """)
            self.stdout.write(self.style.SUCCESS('✓ Created TradingSession table'))
            
            # Create TradingSession_positions_reviewed (many-to-many)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS investing_tradingsession_positions_reviewed (
                    id SERIAL PRIMARY KEY,
                    tradingsession_id INTEGER NOT NULL REFERENCES investing_tradingsession(id) ON DELETE CASCADE,
                    optionsposition_id INTEGER NOT NULL REFERENCES investing_optionsposition(id) ON DELETE CASCADE,
                    UNIQUE (tradingsession_id, optionsposition_id)
                );
            """)
            self.stdout.write(self.style.SUCCESS('✓ Created TradingSession_positions_reviewed table'))
            
            self.stdout.write(self.style.SUCCESS('\n✅ All managed trading tables created successfully!'))

