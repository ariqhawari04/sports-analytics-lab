
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client


ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "data" / "processed" / "salt_epl_matches.csv"

load_dotenv(ROOT / ".env")


def load_app_matches():
    df = pd.read_csv(
        CSV_PATH,
        dtype={
            "season": "string",
            "source": "string",
            "game_id": "string",
        },
    )

    required = [
        "source", "season", "date", "week",
        "home_team", "away_team",
        "home_goals", "away_goals",
    ]

    if df[required].isna().any().any():
        raise ValueError("Missing required match data")

    if df.duplicated(
        ["season", "home_team", "away_team"]
    ).any():
        raise ValueError("Duplicate fixtures detected")

    expected_sources = {
        "2024-25": "openfootball",
        "2025-26": "openfootball",
        "2026-27": "football-data.org",
    }

    if set(df["season"]) != set(expected_sources):
        raise ValueError("Unexpected season coverage")

    for season, expected_source in expected_sources.items():
        season_data = df[df["season"] == season]

        if not (season_data["source"] == expected_source).all():
            raise ValueError(
                f"Unexpected source for {season}"
            )

        print(
            f"{season}: {len(season_data)} matches "
            f"from {expected_source}"
        )

    records = []

    for _, row in df.iterrows():
        match_date = pd.to_datetime(
            row["date"], errors="raise"
        ).date().isoformat()

        record = {
            "league_code": "PL",
            "source": str(row["source"]),
            "season": str(row["season"]),
            "source_game_id": (
                None if pd.isna(row["game_id"])
                else str(row["game_id"])
            ),
            "match_date": match_date,
            "matchweek": int(row["week"]),
            "home_team": str(row["home_team"]),
            "away_team": str(row["away_team"]),
            "home_goals": int(row["home_goals"]),
            "away_goals": int(row["away_goals"]),
        }

        records.append(record)

    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SECRET_KEY"],
    )

    batch_size = 100

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]

        client.table("app_matches").upsert(
            batch,
            on_conflict=(
                "league_code,season,"
                "home_team,away_team,match_date"
            ),
        ).execute()

        print(
            f"Uploaded "
            f"{min(start + batch_size, len(records))}"
            f"/{len(records)}"
        )

    print("\nUpload completed!")


if __name__ == "__main__":
    load_app_matches()
