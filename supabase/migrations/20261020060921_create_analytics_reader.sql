
-- ==========================================
-- SAL v0.2.3
-- Internal Analytics Read-only Role
-- ==========================================

-- Dedicated account for the internal dashboard.
-- Password will be configured separately,
-- never stored in a Git migration.

CREATE ROLE sal_analytics_reader
WITH
    LOGIN
    NOINHERIT
    NOBYPASSRLS
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOREPLICATION;

-- ==========================================
-- DATABASE ACCESS
-- ==========================================

GRANT CONNECT ON DATABASE postgres
TO sal_analytics_reader;

GRANT USAGE ON SCHEMA public
TO sal_analytics_reader;

-- Restrict access to analytics tables.
GRANT SELECT
ON public.product_events,
   public.product_feedback
TO sal_analytics_reader;

-- ==========================================
-- ROW LEVEL SECURITY
-- ==========================================

CREATE POLICY sal_analytics_reader_events_select
ON public.product_events
FOR SELECT
TO sal_analytics_reader
USING (true);

CREATE POLICY sal_analytics_reader_feedback_select
ON public.product_feedback
FOR SELECT
TO sal_analytics_reader
USING (true);
