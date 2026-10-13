-- Master table: football teams
CREATE TABLE public.teams (
    team_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    team_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Premier League match data
CREATE TABLE public.matches (
    match_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source TEXT NOT NULL DEFAULT 'fbref',
    source_game_id TEXT NOT NULL,

    season TEXT NOT NULL,
    matchweek INTEGER,
    match_date DATE NOT NULL,
    kickoff_time TEXT,

    home_team_id BIGINT NOT NULL REFERENCES public.teams(team_id),
    away_team_id BIGINT NOT NULL REFERENCES public.teams(team_id),

    home_goals INTEGER,
    away_goals INTEGER,

    attendance INTEGER,
    venue TEXT,
    referee TEXT,
    match_report TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (source, source_game_id),
    CHECK (home_team_id <> away_team_id),
    CHECK (home_goals >= 0),
    CHECK (away_goals >= 0),
    CHECK (attendance >= 0)
);

CREATE INDEX idx_matches_season
ON public.matches(season);

CREATE INDEX idx_matches_home_team
ON public.matches(home_team_id);

CREATE INDEX idx_matches_away_team
ON public.matches(away_team_id);