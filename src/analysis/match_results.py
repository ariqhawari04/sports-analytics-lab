
"""
SAL v0.3 — Reusable match-to-team analytics.

Supports multiple leagues and seasons.
"""

import pandas as pd


def build_team_results(matches):
    required = [
        "league_code",
        "season",
        "match_date",
        "matchweek",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
    ]

    if matches.empty or matches[required].isna().any().any():
        raise ValueError("Incomplete match data")

    data = matches.copy()

    data["match_date"] = pd.to_datetime(
        data["match_date"], errors="raise"
    )

    home = pd.DataFrame({
        "league_code": data["league_code"],
        "season": data["season"],
        "match_date": data["match_date"],
        "matchweek": data["matchweek"],
        "team": data["home_team"],
        "opponent": data["away_team"],
        "location": "Home",
        "goals_for": data["home_goals"],
        "goals_against": data["away_goals"],
    })

    away = pd.DataFrame({
        "league_code": data["league_code"],
        "season": data["season"],
        "match_date": data["match_date"],
        "matchweek": data["matchweek"],
        "team": data["away_team"],
        "opponent": data["home_team"],
        "location": "Away",
        "goals_for": data["away_goals"],
        "goals_against": data["home_goals"],
    })

    results = pd.concat(
        [home, away], ignore_index=True
    )

    results["result"] = "D"
    results.loc[
        results["goals_for"] > results["goals_against"],
        "result"
    ] = "W"
    results.loc[
        results["goals_for"] < results["goals_against"],
        "result"
    ] = "L"

    results["points"] = results["result"].map({
        "W": 3, "D": 1, "L": 0
    })

    results = results.sort_values(
        [
            "league_code",
            "season",
            "team",
            "match_date",
            "matchweek",
        ],
        kind="stable",
    ).reset_index(drop=True)

    groups = results.groupby(
        ["league_code", "season", "team"]
    )

    results["cumulative_points"] = (
        groups["points"].cumsum()
    )

    results["match_number"] = (
        groups.cumcount() + 1
    )

    return results
