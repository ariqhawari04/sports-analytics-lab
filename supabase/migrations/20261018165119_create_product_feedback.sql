
-- SAL v0.2.1: Product Feedback
-- Stores anonymous user ratings and suggestions

CREATE TABLE public.product_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    page TEXT NOT NULL DEFAULT 'general'
        CHECK (char_length(page) BETWEEN 1 AND 80),

    app_version TEXT NOT NULL DEFAULT 'v0.2.1'
        CHECK (char_length(app_version) BETWEEN 1 AND 20),

    rating SMALLINT
        CHECK (rating BETWEEN 1 AND 5),

    comment TEXT
        CHECK (char_length(comment) <= 1000),

    CONSTRAINT feedback_has_content
        CHECK (
            rating IS NOT NULL
            OR NULLIF(BTRIM(comment), '') IS NOT NULL
        )
);

-- Enable Row Level Security
ALTER TABLE public.product_feedback
ENABLE ROW LEVEL SECURITY;

-- Remove default public permissions
REVOKE ALL ON TABLE public.product_feedback
FROM PUBLIC, anon, authenticated;

-- Anonymous visitors may only submit feedback
GRANT INSERT (page, app_version, rating, comment)
ON TABLE public.product_feedback TO anon;

CREATE POLICY "Allow anonymous feedback submission"
ON public.product_feedback
FOR INSERT
TO anon
WITH CHECK (true);

-- Index for time-based analytics
CREATE INDEX idx_product_feedback_created_at
ON public.product_feedback (created_at DESC);
