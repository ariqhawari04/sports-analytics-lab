
"""
SAL v0.3 — Bundesliga Historical Dataset

Build and validate the 2024/25 Bundesliga
dataset locally.

No database connection or writes.
"""

from pathlib import Path

import pandas as pd

from src.processing.build_public_matches import (
    load_openfootball,
)


ROOT = Path(__file__).resolve().parents[2]

LEAGUE_CODE = "BL1"
SEASON = "2024-25"

EXPECTED_TEAMS = 18
EXPECTED_MATCHES = 306
EXPECTED_WEEKS = 34


def build_bundesliga_preview():

    # 1. Fetch Bundesliga results.
    df = load_openfootball(
        SEASON,
        league_code=LEAGUE_CODE,
    ).copy()

    df.insert(0, "league_code", LEAGUE_CODE)

    # 2. Check required data.
    required = [
        "league_code",
        "season",
        "date",
        "week",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
    ]

    if df.empty or df[required].isna().any().any():
        raise ValueError("Missing required match data")

    # 3. Validate number of matches.
    if len(df) != EXPECTED_MATCHES:
        raise ValueError(
            f"Expected {EXPECTED_MATCHES} matches, "
            f"got {len(df)}"
        )

    # 4. Validate participating clubs.
    teams = (
        set(df["home_team"])
        | set(df["away_team"])
    )

    if len(teams) != EXPECTED_TEAMS:
        raise ValueError(
            f"Expected {EXPECTED_TEAMS} teams, "
            f"got {len(teams)}"
        )

    # 5. Validate matchweeks.
    expected_weeks = set(
        range(1, EXPECTED_WEEKS + 1)
    )

    if set(df["week"]) != expected_weeks:
        raise ValueError("Invalid matchweek coverage")

    matches_per_week = df.groupby("week").size()

    if not (matches_per_week == 9).all():
        raise ValueError(
            "Expected 9 matches per matchweek"
        )

    # 6. Validate fixture uniqueness.
    if df.duplicated([
        "league_code",
        "season",
        "home_team",
        "away_team",
    ]).any():
        raise ValueError("Duplicate fixtures detected")

    if (df["home_team"] == df["away_team"]).any():
        raise ValueError("Invalid same-team fixture")

    # 7. Validate scores.
    if (
        (df["home_goals"] < 0)
        | (df["away_goals"] < 0)
    ).any():
        raise ValueError("Negative score detected")

    # 8. Validate home and away coverage.
    for team in teams:

        home_count = (
            df["home_team"] == team
        ).sum()

        away_count = (
            df["away_team"] == team
        ).sum()

        if home_count != 17 or away_count != 17:
            raise ValueError(
                f"Unexpected fixture count: {team}"
            )

    # 9. Prepare future database schema.
    df = df.rename(columns={
        "date": "match_date",
        "week": "matchweek",
        "game_id": "source_game_id",
    })

    df["match_date"] = pd.to_datetime(
        df["match_date"],
        errors="raise",
    ).dt.strftime("%Y-%m-%d")

    columns = [
        "league_code",
        "season",
        "source",
        "source_game_id",
        "match_date",
        "matchweek",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
    ]

    df = df[columns].sort_values(
        ["match_date", "matchweek", "home_team"]
    ).reset_index(drop=True)

    # 10. Save local preview.
    output_dir = ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = (
        output_dir / "bundesliga_2024-25_preview.csv"
    )

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n=== SAL BUNDESLIGA VALIDATION ===")
    print("League:", LEAGUE_CODE)
    print("Season:", SEASON)
    print("Matches:", len(df))
    print("Teams:", len(teams))
    print("Matchweeks:", df["matchweek"].nunique())
    print("Duplicate fixtures: 0")
    print("Validation: PASSED")
    print("Preview saved:", output_path)
    print("\nNO DATABASE WRITES PERFORMED")

    return df


if __name__ == "__main__":
    build_bundesliga_preview()
