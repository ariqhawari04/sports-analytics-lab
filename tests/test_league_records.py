"""Run with: python -m tests.test_league_records (if tests is a package)."""

import pandas as pd

from src.analysis.league_records import (
    build_club_records,
    get_match_extremes,
    get_club_biggest_wins,
    get_longest_streak_runs,
)

raw = pd.DataFrame([
    ("2025-26", "2025-08-01", 1, "A", "B", 2, 0),
    ("2025-26", "2025-08-02", 1, "C", "D", 0, 0),
    ("2025-26", "2025-08-08", 2, "A", "C", 1, 0),
    ("2025-26", "2025-08-10", 2, "D", "B", 1, 3),
    ("2025-26", "2025-08-15", 3, "B", "A", 1, 1),
    ("2025-26", "2025-08-17", 3, "D", "C", 4, 0),
    ("2025-26", "2025-08-23", 4, "A", "D", 0, 1),
    ("2025-26", "2025-08-24", 4, "B", "C", 3, 2),
    ("2026-27", "2026-08-01", 1, "A", "B", 3, 0),
], columns=[
    "season", "match_date", "matchweek", "home_team", "away_team",
    "home_goals", "away_goals",
])
rows = []
for m in raw.itertuples(index=False):
    for club, where, gf, ga in (
        (m.home_team, "Home", m.home_goals, m.away_goals),
        (m.away_team, "Away", m.away_goals, m.home_goals),
    ):
        result = "W" if gf > ga else ("D" if gf == ga else "L")
        rows.append({
            "season": m.season, "team": club, "location": where,
            "match_date": m.match_date, "matchweek": m.matchweek,
            "goals_for": gf, "goals_against": ga, "result": result,
            "points": {"W": 3, "D": 1, "L": 0}[result],
        })
results = pd.DataFrame(rows).sort_values(
    ["season", "team", "match_date", "matchweek"]
)
results["match_number"] = results.groupby(["season", "team"]).cumcount() + 1

stats = build_club_records(results, "2025-26").set_index("team")
assert stats.loc["A", "Pts"] == 7
assert stats.loc["A", "Clean_Sheets"] == 2
assert stats.loc["A", "Longest_Winning_Streak"] == 2
assert stats.loc["A", "Longest_Unbeaten_Streak"] == 3
assert stats.loc["A", "Home_PPG"] == 2.0
assert stats.loc["A", "Away_PPG"] == 1.0
assert stats.loc["D", "Clean_Sheets"] == 3
assert stats.loc["D", "Longest_Winning_Streak"] == 2

extremes = get_match_extremes(raw, "2025-26")
assert extremes["highest_scoring"].iloc[0]["Total_Goals"] == 5
assert extremes["highest_scoring"].iloc[0]["home_team"] == "B"
assert extremes["biggest_wins"].iloc[0]["Winning_Margin"] == 4
assert extremes["biggest_wins"].iloc[0]["home_team"] == "D"

club_wins = get_club_biggest_wins(raw, "2025-26", "A")
assert len(club_wins) == 1
assert club_wins.iloc[0]["Opponent"] == "B"
assert club_wins.iloc[0]["Winning_Margin"] == 2
assert get_club_biggest_wins(raw, "2025-26", "C").empty
assert build_club_records(results, "2026-27").set_index("team").loc["A", "Longest_Winning_Streak"] == 1

# Equal largest margins should both be included.
tie_data = pd.concat([raw, pd.DataFrame([{
    "season": "2025-26", "match_date": "2026-05-01", "matchweek": 38,
    "home_team": "B", "away_team": "C", "home_goals": 4,
    "away_goals": 0,
}])], ignore_index=True)
assert len(get_match_extremes(tie_data, "2025-26")["biggest_wins"]) == 2


# ==========================================
# TEST STREAK MATCH HISTORY
# ==========================================

winning_runs = get_longest_streak_runs(
    results,
    "2025-26",
    "A",
    streak_type="winning",
)

assert len(winning_runs) == 1
assert len(winning_runs[0]) == 2
assert winning_runs[0]["match_number"].tolist() == [1, 2]
assert winning_runs[0]["result"].tolist() == ["W", "W"]

unbeaten_runs = get_longest_streak_runs(
    results,
    "2025-26",
    "A",
    streak_type="unbeaten",
)

assert len(unbeaten_runs) == 1
assert len(unbeaten_runs[0]) == 3
assert unbeaten_runs[0]["result"].tolist() == [
    "W", "W", "D"
]

# Club C recorded no wins.
assert get_longest_streak_runs(
    results, "2025-26", "C", "winning"
) == []

# Test two equally long winning streaks.
# Deliberately shuffle the row order to confirm
# match_number controls chronology.
tied_streak_data = pd.DataFrame({
    "season": ["2025-26"] * 6,
    "team": ["Test Club"] * 6,
    "match_number": [4, 2, 6, 1, 5, 3],
    "result": ["W", "W", "L", "W", "W", "L"],
})

tied_runs = get_longest_streak_runs(
    tied_streak_data,
    "2025-26",
    "Test Club",
    "winning",
)

assert len(tied_runs) == 2
assert [
    run["match_number"].tolist()
    for run in tied_runs
] == [[1, 2], [4, 5]]

print("Streak history calculations passed!")


print("League records tests passed!")
