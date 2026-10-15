import pandas as pd

from src.analysis.head_to_head import get_head_to_head

sample = pd.DataFrame([
    {
        "season": "2025-26",
        "match_date": "2025-10-01",
        "matchweek": 7,
        "home_team": "Team A",
        "away_team": "Team B",
        "home_goals": 2,
        "away_goals": 1,
    },
    {
        "season": "2025-26",
        "match_date": "2026-02-01",
        "matchweek": 24,
        "home_team": "Team B",
        "away_team": "Team A",
        "home_goals": 0,
        "away_goals": 0,
    },
    {
        "season": "2026-27",
        "match_date": "2026-09-01",
        "matchweek": 4,
        "home_team": "Team B",
        "away_team": "Team A",
        "home_goals": 3,
        "away_goals": 1,
    },
])

summary, meetings = get_head_to_head(
    sample, "Team A", "Team B"
)

assert summary == {
    "matches": 3,
    "team_a_wins": 1,
    "draws": 1,
    "team_b_wins": 1,
}

assert meetings.iloc[0]["season"] == "2026-27"

print("Head-to-Head calculation passed!")