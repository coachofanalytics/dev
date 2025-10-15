-- Add missing contract_submitted_date column if it doesn't exist
ALTER TABLE investing_investor_information 
ADD COLUMN IF NOT EXISTS contract_submitted_date timestamp with time zone DEFAULT NOW() NOT NULL;

-- Verify column was added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name='investing_investor_information' 
  AND column_name='contract_submitted_date';


