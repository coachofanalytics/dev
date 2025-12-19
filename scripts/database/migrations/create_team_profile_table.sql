-- Create TeamProfile table for hybrid team assignment system
-- Can be run safely - includes checks for existing table

-- Drop table if exists (for testing)
-- DROP TABLE IF EXISTS accounts_teamprofile CASCADE;

-- Create TeamProfile table
CREATE TABLE IF NOT EXISTS accounts_teamprofile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    priority INTEGER DEFAULT 0 NOT NULL,
    total_points INTEGER DEFAULT 0 NOT NULL,
    is_manually_assigned BOOLEAN DEFAULT FALSE NOT NULL,
    last_promoted TIMESTAMP WITH TIME ZONE NULL,
    promotion_notes TEXT DEFAULT '' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Foreign key to auth_user (CustomerUser)
    CONSTRAINT fk_teamprofile_user 
        FOREIGN KEY (user_id) 
        REFERENCES auth_user(id) 
        ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_team_priority_points 
    ON accounts_teamprofile(priority, total_points DESC);

CREATE INDEX IF NOT EXISTS idx_team_manual 
    ON accounts_teamprofile(is_manually_assigned);

CREATE INDEX IF NOT EXISTS idx_team_points 
    ON accounts_teamprofile(total_points);

-- Create comments
COMMENT ON TABLE accounts_teamprofile IS 'Team assignment metadata - uses Django Groups for categories';
COMMENT ON COLUMN accounts_teamprofile.priority IS 'Display priority (higher = shown first within category)';
COMMENT ON COLUMN accounts_teamprofile.total_points IS 'Cached total points (recalculated daily)';
COMMENT ON COLUMN accounts_teamprofile.is_manually_assigned IS 'True = manual, False = points-based';

-- Verification query
SELECT 
    COUNT(*) as table_exists,
    (SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'accounts_teamprofile') as index_count
FROM information_schema.tables 
WHERE table_name = 'accounts_teamprofile';

