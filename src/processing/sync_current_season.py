
"""
Sync finished EPL 2026/27 matches to Supabase.

Dry run:
    python -m src.processing.sync_current_season

Apply changes:
    python -m src.processing.sync_current_season --apply
"""

import argparse
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

from src.processing.export_football_data import (
    export_matches,
    OUTPUT_DIR,
)


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

SEASON = "2026-27"
CSV_PATH = OUTPUT_DIR / "football_data_2026_27.csv"

COMPARE_FIELDS = [
    "source_game_id",
    "match_date",
    "matchweek",
    "home_goals",
    "away_goals",
]


def sync_current_season(apply=False):

    print(f"\n=== SAL EPL {SEASON} SYNC ===")

    # 1. Fetch and validate the API response.
    export_matches()

    df = pd.read_csv(
        CSV_PATH,
        dtype={"game_id": "string"},
    )

    required = [
        "game_id", "date", "week",
        "home_team", "away_team",
        "home_goals", "away_goals",
    ]

    if df.empty or df[required].isna().any().any():
        raise ValueError("Incomplete current-season data")

    if df.duplicated(
        ["home_team", "away_team"]
    ).any():
        raise ValueError("Duplicate fixtures in API data")

    # 2. Prepare records for Supabase.
    records = []

    for match in df.itertuples(index=False):

        records.append({
            "league_code": "PL",
            "season": SEASON,
            "source": "football-data.org",
            "source_game_id": str(match.game_id),
            "match_date": str(match.date),
            "matchweek": int(match.week),
            "home_team": str(match.home_team),
            "away_team": str(match.away_team),
            "home_goals": int(match.home_goals),
            "away_goals": int(match.away_goals),
        })

    # 3. Read existing current-season records.
    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SECRET_KEY"],
    )

    response = (
        client.table("app_matches")
        .select(
            "league_code,source_game_id,match_date,matchweek,"
            "home_team,away_team,home_goals,away_goals"
        )
        .eq("league_code", "PL")
        .eq("season", SEASON)
        .limit(1000)
        .execute()
    )

    existing = response.data or []

    existing_by_fixture = {
        (row["home_team"], row["away_team"]): row
        for row in existing
    }

    existing_by_id = {
        str(row["source_game_id"]): row
        for row in existing
        if row["source_game_id"] is not None
    }

    # Fail safely if the API suddenly returns
    # fewer results than our database.
    if len(records) < len(existing):
        raise ValueError(
            "API has fewer finished matches than "
            "Supabase. Manual review required."
        )

    # 4. Find new or changed matches.
    changes = []
    new_count = 0
    updated_count = 0

    for record in records:

        fixture_key = (
            record["home_team"],
            record["away_team"],
        )

        previous = existing_by_fixture.get(fixture_key)

        # A date change needs explicit review because
        # match_date is part of the new unique key.
        if previous is not None and (
            str(previous["match_date"])
            != record["match_date"]
        ):
            raise ValueError(
                "Match date changed for match ID "
                f"{record['source_game_id']}. "
                "Review before syncing."
            )

        # Detect a renamed fixture with an existing ID.
        previous_id = existing_by_id.get(
            record["source_game_id"]
        )

        if previous_id is not None:
            old_key = (
                previous_id["home_team"],
                previous_id["away_team"],
            )

            if old_key != fixture_key:
                raise ValueError(
                    "Team name changed for match ID "
                    f"{record['source_game_id']}"
                )

        if previous is None:
            changes.append(record)
            new_count += 1
            continue

        if any(
            str(previous[field]) != str(record[field])
            for field in COMPARE_FIELDS
        ):
            changes.append(record)
            updated_count += 1

    print(f"API finished matches: {len(records)}")
    print(f"Supabase matches:     {len(existing)}")
    print(f"New matches:          {new_count}")
    print(f"Changed matches:      {updated_count}")

    if not changes:
        print("Already up to date. No writes needed.")
        return

    # 5. Only write when --apply is explicitly set.
    if not apply:
        print("DRY RUN: no database changes made.")
        return

    for start in range(0, len(changes), 100):
        batch = changes[start:start + 100]

        (
            client.table("app_matches")
            .upsert(
                batch,
                on_conflict=(
                    "league_code,season,"
                    "home_team,away_team,match_date"
                ),
            )
            .execute()
        )

    print(f"SUCCESS: {len(changes)} records synced.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to Supabase",
    )

    args = parser.parse_args()

    sync_current_season(apply=args.apply)
