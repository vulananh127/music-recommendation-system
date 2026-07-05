-- Load FP-Growth rules into database
-- This script assumes rules CSV files are in the correct PostgreSQL array format

BEGIN;

-- Truncate existing rules
TRUNCATE fp_rules_tracks, fp_rules_artists CASCADE;

-- Note: CSV files need to be preprocessed to convert Python list format to PostgreSQL array format
-- Python format: ['spotify:track:xxx']
-- PostgreSQL format: {spotify:track:xxx}

-- Manual load instructions:
-- 1. Convert CSV format using Python or sed
-- 2. Use \copy command from psql

COMMIT;
