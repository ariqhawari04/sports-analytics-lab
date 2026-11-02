
"""
SAL v0.3 — Multi-League Dataset Builder

Build validated historical league datasets locally.
No database connections or writes.
"""

from pathlib import Path

import pandas as pd

from src.processing.build_public_matches import (
    load_openfootball,
)
from src.analysis.match_results import build_team_results
from src.analysis.standings import build_standings


ROOT = Path(__file__).resolve().parents[2]

SEASON_COVERAGE = {
    "2023-24": ["BL1", "FL1", "PD", "SA"],
    "2024-25": ["BL1", "FL1"],
}



LEAGUES = {
    "BL1": {
        "name": "Bundesliga",
        "teams": 18,
        "weeks": 34,
    },
    "FL1": {
        "name": "Ligue 1",
        "teams": 18,
        "weeks": 34,
    },
    "PD": {
        "name": "La Liga",
        "teams": 20,
        "weeks": 38,
    },
    "SA": {
        "name": "Serie A",
        "teams": 20,
        "weeks": 38,
    },
}



def validate_league(df, code, config):
    teams = set(df["home_team"]) | set(df["away_team"])
    expected_matches = (
        config["teams"] * config["weeks"] // 2
    )

    required = [
        "season", "date", "week",
        "home_team", "away_team",
        "home_goals", "away_goals",
    ]

    if df.empty or df[required].isna().any().any():
        raise ValueError(f"{code}: missing data")

    if len(df) != expected_matches:
        raise ValueError(
            f"{code}: incomplete match coverage"
        )

    if len(teams) != config["teams"]:
        raise ValueError(
            f"{code}: unexpected number of teams"
        )

    if set(df["week"]) != set(
        range(1, config["weeks"] + 1)
    ):
        raise ValueError(
            f"{code}: invalid matchweek coverage"
        )

    if not (
        df.groupby("week").size()
        == config["teams"] // 2
    ).all():
        raise ValueError(
            f"{code}: invalid matches per week"
        )

    if df.duplicated([
        "season", "home_team", "away_team"
    ]).any():
        raise ValueError(
            f"{code}: duplicate fixtures"
        )

    if (df["home_team"] == df["away_team"]).any():
        raise ValueError(
            f"{code}: invalid same-team fixture"
        )

    if (
        (df["home_goals"] < 0)
        | (df["away_goals"] < 0)
    ).any():
        raise ValueError(
            f"{code}: negative goals"
        )

    expected_home = (config["teams"] - 1)

    for team in teams:
        home = (df["home_team"] == team).sum()
        away = (df["away_team"] == team).sum()

        if home != expected_home or away != expected_home:
            raise ValueError(
                f"{code}: invalid fixture count for {team}"
            )



def main():
    frames = []

    for season, league_codes in SEASON_COVERAGE.items():
        for code in league_codes:
            config = LEAGUES[code]

            # 1. Fetch and validate source data.
            df = load_openfootball(
                season,
                league_code=code,
            ).copy()

            validate_league(df, code, config)

            df.insert(0, "league_code", code)

            # 2. Standardize the schema.
            df = df.rename(columns={
                "date": "match_date",
                "week": "matchweek",
                "game_id": "source_game_id",
            })

            df["match_date"] = pd.to_datetime(
                df["match_date"],
                errors="raise",
            )

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

            df = df[columns]

            # 3. Validate calculated standings.
            results = build_team_results(df)
            standings = build_standings(results)

            if (
                len(standings) != config["teams"]
                or not (
                    standings["MP"] == config["weeks"]
                ).all()
            ):
                raise ValueError(
                    f"{code} {season}: standings failed"
                )

            print(
                f"{season} | {config['name']}: PASSED | "
                f"{len(df)} matches | "
                f"Winner: {standings.iloc[0]['team']}"
            )

            frames.append(df)

    # 4. Combine all validated league-seasons.
    combined = pd.concat(
        frames, ignore_index=True
    )

    unique_columns = [
        "league_code",
        "season",
        "home_team",
        "away_team",
        "match_date",
    ]

    if combined.duplicated(unique_columns).any():
        raise ValueError(
            "Duplicate multi-league records"
        )

    expected_total = sum(
        LEAGUES[code]["teams"]
        * LEAGUES[code]["weeks"] // 2
        for codes in SEASON_COVERAGE.values()
        for code in codes
    )

    if len(combined) != expected_total:
        raise ValueError(
            "Unexpected combined match count"
        )

    # 5. Save local CSV preview only.
    output_dir = ROOT / "data" / "processed"
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir
        / "multi_league_historical_preview.csv"
    )

    combined = combined.sort_values(
        ["season", "league_code", "match_date"]
    ).reset_index(drop=True)

    combined.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n=== MULTI-LEAGUE SUMMARY ===")
    print(
        combined.groupby(
            ["season", "league_code"]
        ).size()
    )

    print("Total matches:", len(combined))
    print("Saved:", output_path)
    print("NO DATABASE WRITES PERFORMED")


if __name__ == "__main__":
    main()

