-- SALT public application match dataset
-- Sources: OpenFootball and football-data.org

CREATE TABLE public.app_matches (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    season TEXT NOT NULL,
    source TEXT NOT NULL,
    source_game_id TEXT,

    match_date DATE NOT NULL,
    matchweek SMALLINT NOT NULL,

    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,

    home_goals SMALLINT NOT NULL,
    away_goals SMALLINT NOT NULL,

    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT app_matches_unique_fixture
        UNIQUE (season, home_team, away_team),

    CONSTRAINT app_matches_valid_week
        CHECK (matchweek BETWEEN 1 AND 38),

    CONSTRAINT app_matches_valid_goals
        CHECK (home_goals >= 0 AND away_goals >= 0),

    CONSTRAINT app_matches_different_teams
        CHECK (home_team <> away_team)
);

-- Improve queries filtering by season and date
CREATE INDEX app_matches_season_date_idx
ON public.app_matches (season, match_date);

-- Restrict direct access
ALTER TABLE public.app_matches
ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.app_matches
FROM anon, authenticated;

-- Server-side ETL and app access
GRANT ALL ON public.app_matches TO service_role;

GRANT USAGE, SELECT
ON SEQUENCE public.app_matches_id_seq
TO service_role;
