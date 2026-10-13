
CREATE OR REPLACE VIEW public.league_standings
WITH (security_invoker = true)
AS
WITH team_results AS (
    -- Home team perspective
    SELECT
        season,
        home_team_id AS team_id,
        home_goals AS goals_for,
        away_goals AS goals_against,
        CASE WHEN home_goals > away_goals THEN 1 ELSE 0 END AS win,
        CASE WHEN home_goals = away_goals THEN 1 ELSE 0 END AS draw,
        CASE WHEN home_goals < away_goals THEN 1 ELSE 0 END AS loss
    FROM public.matches
    WHERE home_goals IS NOT NULL
      AND away_goals IS NOT NULL

    UNION ALL

    -- Away team perspective
    SELECT
        season,
        away_team_id AS team_id,
        away_goals AS goals_for,
        home_goals AS goals_against,
        CASE WHEN away_goals > home_goals THEN 1 ELSE 0 END AS win,
        CASE WHEN away_goals = home_goals THEN 1 ELSE 0 END AS draw,
        CASE WHEN away_goals < home_goals THEN 1 ELSE 0 END AS loss
    FROM public.matches
    WHERE home_goals IS NOT NULL
      AND away_goals IS NOT NULL
),
aggregated AS (
    SELECT
        season,
        team_id,
        COUNT(*) AS played,
        SUM(win) AS wins,
        SUM(draw) AS draws,
        SUM(loss) AS losses,
        SUM(goals_for) AS gf,
        SUM(goals_against) AS ga,
        SUM(goals_for - goals_against) AS gd,
        SUM(win) * 3 + SUM(draw) AS points
    FROM team_results
    GROUP BY season, team_id
)
SELECT
    a.season,
    ROW_NUMBER() OVER (
        PARTITION BY a.season
        ORDER BY a.points DESC,
                 a.gd DESC,
                 a.gf DESC,
                 t.team_name ASC
    ) AS position,
    t.team_name,
    a.played,
    a.wins,
    a.draws,
    a.losses,
    a.gf,
    a.ga,
    a.gd,
    a.points
FROM aggregated a
JOIN public.teams t ON a.team_id = t.team_id;
