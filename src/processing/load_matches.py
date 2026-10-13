
import os
import re
import argparse
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"

load_dotenv(ROOT / ".env")

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SECRET_KEY"]
)


def parse_score(score):
    if pd.isna(score) or str(score).strip() == "":
        return None, None

    match = re.fullmatch(
        r"\s*(\d+)\s*[-–—]\s*(\d+)\s*",
        str(score)
    )

    if not match:
        raise ValueError(f"Unexpected score: {score}")

    return int(match.group(1)), int(match.group(2))


def optional_text(value):
    return None if pd.isna(value) else str(value)


def optional_int(value):
    return None if pd.isna(value) else int(value)


def load_season(season, dry_run=False):
    season_label = season.replace("-", "_")
    csv_path = RAW_DIR / f"fbref_schedule_{season_label}.csv"

    df = pd.read_csv(csv_path, dtype={"season": str})

    print(f"\n=== SEASON {season} ===")
    print(f"Fixtures: {len(df)}")

    # Data quality checks
    assert len(df) == 380, "Expected 380 Premier League fixtures"

    expected_code = season[2:4] + season[5:7]
    observed_codes = set(df["season"].dropna().astype(str))

    if observed_codes != {expected_code}:
        raise ValueError(
            f"Unexpected season codes: {observed_codes}"
        )

    if df["home_team"].isna().any() or df["away_team"].isna().any():
        raise ValueError("Missing team names")

    if df["date"].isna().any():
        raise ValueError("Missing match dates")

    # Extract unique clubs
    team_names = sorted(
        set(df["home_team"]) | set(df["away_team"])
    )

    if len(team_names) != 20:
        raise ValueError(
            f"Expected 20 teams, found {len(team_names)}"
        )

    # Validate all fixtures before uploading anything
    records = []

    for _, row in df.iterrows():
        home_goals, away_goals = parse_score(row["score"])

        match_date = pd.to_datetime(
            row["date"], errors="raise"
        ).date().isoformat()

        records.append({
            "source": "fbref",
            "source_game_id": optional_text(row["game_id"]),
            "season": season,
            "matchweek": optional_int(row["week"]),
            "match_date": match_date,
            "kickoff_time": optional_text(row["time"]),
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "home_goals": home_goals,
            "away_goals": away_goals,
            "attendance": optional_int(row["attendance"]),
            "venue": optional_text(row["venue"]),
            "referee": optional_text(row["referee"]),
            "match_report": optional_text(row["match_report"]),
        })

    completed = sum(
        r["home_goals"] is not None
        and r["away_goals"] is not None
        for r in records
    )

    # Fixtures without game IDs cannot be safely upserted
    uploadable = [
        r for r in records if r["source_game_id"]
    ]

    skipped = len(records) - len(uploadable)

    ids = [r["source_game_id"] for r in uploadable]

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate FBref game IDs")

    print(f"Teams: {len(team_names)}")
    print(f"Completed matches: {completed}")
    print(f"Upcoming/unscored: {len(records) - completed}")
    print(f"Rows with game IDs: {len(uploadable)}")
    print(f"Skipped (missing game ID): {skipped}")

    if dry_run:
        print("DRY RUN: No database changes")
        return

    # Upsert teams
    supabase.table("teams").upsert(
        [{"team_name": name} for name in team_names],
        on_conflict="team_name"
    ).execute()

    # Get team IDs from PostgreSQL
    result = (
        supabase.table("teams")
        .select("team_id,team_name")
        .execute()
    )

    team_mapping = {
        row["team_name"]: row["team_id"]
        for row in result.data
    }

    # Replace team names with foreign keys
    match_records = []

    for record in uploadable:
        record = record.copy()

        record["home_team_id"] = team_mapping[
            record.pop("home_team")
        ]

        record["away_team_id"] = team_mapping[
            record.pop("away_team")
        ]

        match_records.append(record)

    # Batch upsert
    batch_size = 100

    for start in range(0, len(match_records), batch_size):
        batch = match_records[start:start + batch_size]

        supabase.table("matches").upsert(
            batch,
            on_conflict="source,source_game_id"
        ).execute()

        print(
            f"Uploaded {min(start + batch_size, len(match_records))}"
            f"/{len(match_records)}"
        )

    print(f"Season {season} completed!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--seasons",
        nargs="+",
        default=["2025-26", "2026-27"]
    )

    parser.add_argument(
        "--dry-run",
        action="store_true"
    )

    args = parser.parse_args()

    for season in args.seasons:
        load_season(season, dry_run=args.dry_run)
