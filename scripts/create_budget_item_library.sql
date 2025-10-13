-- Manual SQL to create BudgetItemLibrary table in UAT
-- This bypasses the migration conflict

CREATE TABLE IF NOT EXISTS finance_budgetitemlibrary (
    id SERIAL PRIMARY KEY,
    item_name VARCHAR(200) NOT NULL,
    description TEXT,
    typical_amount DECIMAL(12,2),
    unit_type VARCHAR(50) DEFAULT 'each',
    usage_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    category_id INTEGER NOT NULL REFERENCES finance_budgetcategory(id) ON DELETE CASCADE,
    subcategory_id INTEGER NOT NULL REFERENCES finance_budgetsubcategory(id) ON DELETE CASCADE,
    CONSTRAINT finance_budgetitemlibrary_category_subcategory_item_name_unique 
        UNIQUE (category_id, subcategory_id, item_name)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS finance_budgetitemlibrary_category_id_idx 
    ON finance_budgetitemlibrary(category_id);
CREATE INDEX IF NOT EXISTS finance_budgetitemlibrary_subcategory_id_idx 
    ON finance_budgetitemlibrary(subcategory_id);
CREATE INDEX IF NOT EXISTS finance_budgetitemlibrary_is_active_idx 
    ON finance_budgetitemlibrary(is_active);
CREATE INDEX IF NOT EXISTS finance_budgetitemlibrary_usage_count_idx 
    ON finance_budgetitemlibrary(usage_count DESC);

-- Add comments
COMMENT ON TABLE finance_budgetitemlibrary IS 'Master library of budget items for cascading dropdowns';
COMMENT ON COLUMN finance_budgetitemlibrary.item_name IS 'Name of the budget item (e.g., Safaricom internet subscription)';
COMMENT ON COLUMN finance_budgetitemlibrary.typical_amount IS 'Typical/average amount based on historical data';
COMMENT ON COLUMN finance_budgetitemlibrary.usage_count IS 'Number of times this item has been used (for sorting)';
COMMENT ON COLUMN finance_budgetitemlibrary.is_active IS 'Whether this item is active and available for selection';

-- Verify table creation
SELECT 'BudgetItemLibrary table created successfully' as status;
SELECT COUNT(*) as existing_records FROM finance_budgetitemlibrary;
