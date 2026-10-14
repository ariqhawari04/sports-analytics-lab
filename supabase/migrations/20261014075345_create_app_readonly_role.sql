-- ==========================================
-- SPORTS ANALYTICS LAB
-- Read-only PostgreSQL role
-- ==========================================

-- Create a restricted role.
-- No password is stored in GitHub.
CREATE ROLE sports_app_reader
WITH
    NOLOGIN
    NOINHERIT
    NOBYPASSRLS
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE;

-- Allow connection to the database
GRANT CONNECT ON DATABASE postgres
TO sports_app_reader;

-- Allow access to public schema
GRANT USAGE ON SCHEMA public
TO sports_app_reader;

-- Allow reading application matches only
GRANT SELECT ON public.app_matches
TO sports_app_reader;

-- Explicitly deny write operations
REVOKE INSERT, UPDATE, DELETE, TRUNCATE
ON public.app_matches
FROM sports_app_reader;

-- Enable RLS (already enabled previously)
ALTER TABLE public.app_matches
ENABLE ROW LEVEL SECURITY;

-- Allow this role to read app_matches
CREATE POLICY sports_app_reader_select
ON public.app_matches
FOR SELECT
TO sports_app_reader
USING (true);
