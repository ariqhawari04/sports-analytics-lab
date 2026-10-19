
-- ==========================================
-- SAL v0.2.2 - Product Analytics Events
-- ==========================================

CREATE TABLE public.product_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    session_id UUID NOT NULL,

    event_name TEXT NOT NULL
        CHECK (
            event_name IN (
                'session_start',
                'tab_view'
            )
        ),

    page TEXT
        CHECK (
            page IS NULL
            OR char_length(page) BETWEEN 1 AND 80
        ),

    app_version TEXT NOT NULL DEFAULT 'v0.2.2'
        CHECK (
            char_length(app_version) BETWEEN 1 AND 20
        ),

    CONSTRAINT tab_view_requires_page
        CHECK (
            event_name <> 'tab_view'
            OR page IS NOT NULL
        )
);

-- ==========================================
-- ROW LEVEL SECURITY
-- ==========================================

ALTER TABLE public.product_events
ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.product_events
FROM PUBLIC, anon, authenticated;

-- Public application may submit events only
GRANT INSERT (
    session_id,
    event_name,
    page,
    app_version
)
ON TABLE public.product_events TO anon;

CREATE POLICY "Allow anonymous event submission"
ON public.product_events
FOR INSERT
TO anon
WITH CHECK (true);

-- ==========================================
-- ANALYTICS INDEXES
-- ==========================================

CREATE INDEX idx_product_events_name_created
ON public.product_events (
    event_name,
    created_at DESC
);

CREATE INDEX idx_product_events_page_created
ON public.product_events (
    page,
    created_at DESC
);
