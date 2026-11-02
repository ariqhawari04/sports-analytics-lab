-- Sports Analytics Lab v0.3
-- Prepare app_matches for multiple leagues.
-- Do not apply until ETL and read logic are updated.

BEGIN;

-- Existing EPL records automatically receive PL.
ALTER TABLE public.app_matches
ADD COLUMN league_code TEXT NOT NULL DEFAULT 'PL';

-- The old uniqueness rule assumes that each
-- home-away pairing happens once per season.
ALTER TABLE public.app_matches
DROP CONSTRAINT app_matches_unique_fixture;

-- Allow repeat home-away fixtures on different dates
-- and distinguish matches from different leagues.
ALTER TABLE public.app_matches
ADD CONSTRAINT app_matches_unique_league_fixture_date
UNIQUE (
    league_code,
    season,
    home_team,
    away_team,
    match_date
);

-- Speed up league and season filtering.
CREATE INDEX app_matches_league_season_date_idx
ON public.app_matches (
    league_code,
    season,
    match_date
);

-- Prevent duplicate provider match IDs.
-- NULL IDs remain allowed for OpenFootball data.
CREATE UNIQUE INDEX app_matches_provider_match_uidx
ON public.app_matches (
    league_code,
    season,
    source,
    source_game_id
)
WHERE source_game_id IS NOT NULL;

COMMIT;
