
"""
SAL v0.3 — Staging Multi-League Uploader

Default: dry run, no database writes.
Writes require --apply and project confirmation.

Never uses production credentials.
"""

import argparse
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from dotenv import dotenv_values
from supabase import create_client


ROOT = Path(__file__).resolve().parents[2]

CSV_PATH = (
    ROOT / "data" / "processed"
    / "multi_league_historical_preview.csv"
)

EXPECTED = {
    ("2023-24", "BL1"): 306,
    ("2023-24", "FL1"): 306,
    ("2023-24", "PD"): 380,
    ("2023-24", "SA"): 380,
    ("2024-25", "BL1"): 306,
    ("2024-25", "FL1"): 306,
}

CONFLICT_COLUMNS = (
    "league_code,season,"
    "home_team,away_team,match_date"
)


def load_dataset():
    df = pd.read_csv(CSV_PATH)

    required = [
        "league_code", "season", "source",
        "source_game_id", "match_date", "matchweek",
        "home_team", "away_team",
        "home_goals", "away_goals",
    ]

    if not set(required).issubset(df.columns):
        raise ValueError("Missing required CSV columns")

    nonnullable = [
        col for col in required
        if col != "source_game_id"
    ]

    if df.empty or df[nonnullable].isna().any().any():
        raise ValueError("Incomplete historical dataset")

    coverage = df.groupby(
        ["season", "league_code"]
    ).size().to_dict()

    if coverage != EXPECTED:
        raise ValueError(
            f"Unexpected league-season coverage: {coverage}"
        )

    if not df["source"].eq("openfootball").all():
        raise ValueError("Unexpected data source")

    if df["source_game_id"].notna().any():
        raise ValueError(
            "Expected null provider IDs for OpenFootball"
        )

    df["match_date"] = pd.to_datetime(
        df["match_date"], errors="raise"
    ).dt.strftime("%Y-%m-%d")

    for col in ["matchweek", "home_goals", "away_goals"]:
        df[col] = pd.to_numeric(df[col], errors="raise")

        if (df[col] % 1 != 0).any():
            raise ValueError(f"Invalid integer values: {col}")

        df[col] = df[col].astype(int)

    if (
        (df["home_goals"] < 0).any()
        or (df["away_goals"] < 0).any()
    ):
        raise ValueError("Negative goal values")

    if (df["home_team"] == df["away_team"]).any():
        raise ValueError("Invalid same-team fixture")

    if df.duplicated([
        "league_code", "season",
        "home_team", "away_team", "match_date",
    ]).any():
        raise ValueError("Duplicate match records")

    records = []

    for row in df.itertuples(index=False):
        records.append({
            "league_code": row.league_code,
            "season": row.season,
            "source": row.source,
            "source_game_id": None,
            "match_date": row.match_date,
            "matchweek": row.matchweek,
            "home_team": row.home_team,
            "away_team": row.away_team,
            "home_goals": row.home_goals,
            "away_goals": row.away_goals,
        })

    return records, coverage


def staging_connection():
    config = dotenv_values(ROOT / ".env.staging")
    production = dotenv_values(ROOT / ".env")

    url = (
        config.get("STAGING_SUPABASE_URL") or ""
    ).strip().rstrip("/")

    key = config.get("STAGING_SUPABASE_SECRET_KEY")
    ref = (
        config.get("STAGING_PROJECT_REF") or ""
    ).strip()

    production_url = (
        production.get("SUPABASE_URL") or ""
    ).strip().rstrip("/")

    if (
        not ref
        or not key
        or urlparse(url).scheme != "https"
        or urlparse(url).hostname != f"{ref}.supabase.co"
    ):
        raise ValueError("Invalid staging configuration")

    if production_url and url == production_url:
        raise ValueError(
            "SAFETY STOP: staging URL matches production!"
        )

    return create_client(url, key), ref


def count_records(client):
    response = (
        client.table("app_matches")
        .select("id", count="exact")
        .limit(1)
        .execute()
    )

    if response.count is None:
        raise ValueError("Unable to verify staging row count")

    return response.count


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write records to staging",
    )

    parser.add_argument(
        "--confirm-project-ref",
        default="",
        help="Explicitly confirm the target project",
    )

    args = parser.parse_args()

    records, coverage = load_dataset()
    client, project_ref = staging_connection()

    before = count_records(client)

    print("\n=== SAL MULTI-LEAGUE STAGING ===")
    print("Target project:", project_ref)
    print("Dataset records:", len(records))
    print("Staging records before:", before)

    print("\nValidated coverage:")
    for (season, league), count in sorted(coverage.items()):
        print(f"{season} | {league}: {count}")

    if not args.apply:
        print("\nDRY RUN: PASSED")
        print("NO DATABASE WRITES PERFORMED")
        return

    if args.confirm_project_ref != project_ref:
        raise ValueError(
            "SAFETY STOP: project confirmation required"
        )

    # Allow first upload or complete idempotent reruns.
    # Partial uploads require manual review.
    if before not in (0, len(records)):
        raise ValueError(
            "SAFETY STOP: unexpected existing row count. "
            "Review staging before retrying."
        )

    batch_size = 100

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]

        (
            client.table("app_matches")
            .upsert(
                batch,
                on_conflict=CONFLICT_COLUMNS,
            )
            .execute()
        )

        print(
            f"Uploaded {min(start + batch_size, len(records))}"
            f"/{len(records)}"
        )

    after = count_records(client)

    if after != len(records):
        raise ValueError(
            f"Unexpected staging count: {after}"
        )

    for (season, league), expected_count in EXPECTED.items():
        response = (
            client.table("app_matches")
            .select("id", count="exact")
            .eq("season", season)
            .eq("league_code", league)
            .limit(1)
            .execute()
        )

        if response.count != expected_count:
            raise ValueError(
                f"{league} {season}: "
                "staging count mismatch"
            )

    print("\nSTAGING UPLOAD: PASSED")
    print("Verified records:", after)


if __name__ == "__main__":
    main()
