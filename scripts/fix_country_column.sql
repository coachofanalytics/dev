-- Fix missing country column in accounts_userprofile table
ALTER TABLE accounts_userprofile ADD COLUMN IF NOT EXISTS country VARCHAR(2) NULL;


