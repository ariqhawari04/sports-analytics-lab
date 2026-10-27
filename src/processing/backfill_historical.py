
"""
SAL — Historical EPL Backfill

Load and validate 2015/16–2023/24 Premier League
matches before optionally uploading to Supabase.

Dry run:
    python -m src.processing.backfill_historical

Upload:
    python -m src.processing.backfill_historical --apply
"""

import argparse
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

from src.processing.build_public_matches import (
    load_openfootball,
    validate_season,
)


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

NEW_SEASONS = [
    f"{year}-{(year + 1) % 100:02d}"
    for year in range(2015, 2024)
]

# Match names from historical OpenFootball files
# to the canonical club names used by SAL.
TEAM_ALIASES = {
    "Aston Villa": "Aston Villa FC",
    "Brighton & Hove Albion": "Brighton & Hove Albion FC",
    "Cardiff City": "Cardiff City FC",
    "Crystal Palace": "Crystal Palace FC",
    "Huddersfield Town": "Huddersfield Town AFC",
    "Hull City": "Hull City AFC",
    "Leicester City": "Leicester City FC",
    "Manchester City": "Manchester City FC",
    "Manchester United": "Manchester United FC",
    "Newcastle United": "Newcastle United FC",
    "Norwich City": "Norwich City FC",
    "Sheffield United": "Sheffield United FC",
    "Stoke City": "Stoke City FC",
    "Swansea City": "Swansea City AFC",
    "Tottenham Hotspur": "Tottenham Hotspur FC",
    "West Bromwich Albion": "West Bromwich Albion FC",
    "West Ham United": "West Ham United FC",
    "Wolverhampton Wanderers": "Wolverhampton Wanderers FC",
}

# Independent season-level sanity checks for MU.
EXPECTED_MU_POINTS = {
    "2015-16": 66,
    "2016-17": 69,
    "2017-18": 81,
    "2018-19": 66,
    "2019-20": 66,
    "2020-21": 74,
    "2021-22": 58,
    "2022-23": 75,
    "2023-24": 60,
}


def normalize_team_names(df):
    df = df.copy()

    for column in ["home_team", "away_team"]:
        df[column] = df[column].replace(
            TEAM_ALIASES
        )

    return df


def validate_historical_season(df, season):
    # Existing SAL checks.
    validate_season(df, season)

    if not df["week"].between(1, 38).all():
        raise ValueError(
            f"{season}: invalid matchweek"
        )

    if (
        (df["home_goals"] < 0)
        | (df["away_goals"] < 0)
    ).any():
        raise ValueError(
            f"{season}: negative score detected"
        )

    if (df["home_team"] == df["away_team"]).any():
        raise ValueError(
            f"{season}: invalid same-team fixture"
        )

    clubs = (
        set(df["home_team"])
        | set(df["away_team"])
    )

    # Complete EPL seasons have exactly
    # 19 home and 19 away fixtures per club.
    for club in clubs:
        home_count = (
            df["home_team"] == club
        ).sum()

        away_count = (
            df["away_team"] == club
        ).sum()

        if home_count != 19 or away_count != 19:
            raise ValueError(
                f"{season}: unexpected fixture "
                f"coverage for {club}"
            )

    # Independent MU points check.
    mu = df.loc[
        (df["home_team"] == "Manchester United FC")
        | (df["away_team"] == "Manchester United FC")
    ]

    mu_points = 0

    for match in mu.itertuples(index=False):
        at_home = (
            match.home_team == "Manchester United FC"
        )

        gf = (
            match.home_goals
            if at_home else match.away_goals
        )

        ga = (
            match.away_goals
            if at_home else match.home_goals
        )

        mu_points += (
            3 if gf > ga
            else 1 if gf == ga
            else 0
        )

    if (
        len(mu) != 38
        or mu_points != EXPECTED_MU_POINTS[season]
    ):
        raise ValueError(
            f"{season}: MU validation failed"
        )


def prepare_historical_data():
    frames = []

    # All seasons must pass validation before
    # any database write can happen.
    for season in NEW_SEASONS:

        df = load_openfootball(season)
        df = normalize_team_names(df)

        validate_historical_season(df, season)

        frames.append(df)

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    if len(combined) != len(NEW_SEASONS) * 380:
        raise ValueError(
            "Unexpected historical match count"
        )

    if combined.duplicated(
        ["season", "home_team", "away_team"]
    ).any():
        raise ValueError(
            "Duplicate historical fixtures"
        )

    combined = combined.sort_values(
        ["season", "date", "week", "home_team"]
    ).reset_index(drop=True)

    # Local preview for manual inspection.
    output_dir = ROOT / "data" / "processed"
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    preview_path = (
        output_dir / "historical_backfill_preview.csv"
    )

    combined.to_csv(
        preview_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n=== HISTORICAL BACKFILL SUMMARY ===")
    print(combined.groupby("season").size())
    print("Total matches:", len(combined))
    print("Preview saved:", preview_path)

    return combined


def upload_historical_data(df):
    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SECRET_KEY"],
    )

    records = []

    for row in df.itertuples(index=False):
        records.append({
            "league_code": "PL",
            "source": "openfootball",
            "season": str(row.season),
            "source_game_id": None,
            "match_date": str(row.date),
            "matchweek": int(row.week),
            "home_team": str(row.home_team),
            "away_team": str(row.away_team),
            "home_goals": int(row.home_goals),
            "away_goals": int(row.away_goals),
        })

    for start in range(0, len(records), 100):
        batch = records[start:start + 100]


        client.table("app_matches").upsert(
            batch,
            on_conflict=(
                "league_code,season,"
                "home_team,away_team,match_date"
            ),
        ).execute()

        print(
            f"Uploaded {min(start + 100, len(records))}"
            f"/{len(records)}"
        )

    print("\nHistorical backfill completed!")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Upload validated historical data",
    )

    args = parser.parse_args()

    historical_data = prepare_historical_data()

    if args.apply:
        upload_historical_data(historical_data)
    else:
        print(
            "\nDRY RUN: No changes made to Supabase."
        )


if __name__ == "__main__":
    main()
