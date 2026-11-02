
"""
SAL v0.3 — Production Multi-League Uploader

Dry-run by default.
Writes require --apply and explicit project confirmation.
"""

import argparse
from pathlib import Path
from urllib.parse import urlparse

from dotenv import dotenv_values
from supabase import create_client

from src.processing.upload_multi_league_staging import (
    load_dataset,
    EXPECTED,
    CONFLICT_COLUMNS,
)


ROOT = Path(__file__).resolve().parents[2]
STAGING_REF = "xlhoyrwxfyggyrufvzcb"


def production_connection():
    config = dotenv_values(ROOT / ".env")

    url = (config.get("SUPABASE_URL") or "").strip().rstrip("/")
    key = config.get("SUPABASE_SECRET_KEY")

    parsed = urlparse(url)
    host = parsed.hostname or ""

    if (
        parsed.scheme != "https"
        or not host.endswith(".supabase.co")
        or not key
    ):
        raise ValueError("Invalid production configuration")

    project_ref = host.removesuffix(".supabase.co")


    if project_ref != "jsjekritfzjrfitzkenn":
        raise ValueError(
            "SAFETY STOP: Unexpected production project!"
        )


    staging = dotenv_values(ROOT / ".env.staging")
    staging_url = (
        staging.get("STAGING_SUPABASE_URL") or ""
    ).strip().rstrip("/")

    if (
        project_ref == STAGING_REF
        or url == staging_url
    ):
        raise ValueError(
            "SAFETY STOP: Target is the staging database"
        )

    return create_client(url, key), project_ref


def row_count(client, league=None, season=None):
    query = (
        client.table("app_matches")
        .select("id", count="exact")
    )

    if league:
        query = query.eq("league_code", league)

    if season:
        query = query.eq("season", season)

    response = query.limit(1).execute()

    if response.count is None:
        raise ValueError("Could not verify database count")

    return response.count


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-project-ref", default="")

    args = parser.parse_args()

    records, coverage = load_dataset()
    client, project_ref = production_connection()

    total_before = row_count(client)
    epl_before = row_count(client, league="PL")
    other_before = total_before - epl_before

    print("\n=== SAL PRODUCTION UPLOAD ===")
    print("Target project:", project_ref)
    print("EPL records:", epl_before)
    print("Other league records:", other_before)
    print("Validated upload records:", len(records))

    for (season, league), count in sorted(coverage.items()):
        print(f"{season} | {league}: {count}")

    # Protect all existing Premier League data.
    if epl_before < 4269:
        raise ValueError(
            "SAFETY STOP: Unexpected EPL record count"
        )

    # First production upload only.
    if other_before != 0:
        raise ValueError(
            "SAFETY STOP: Non-EPL records already exist"
        )

    if not args.apply:
        print("\nPRODUCTION DRY RUN: PASSED")
        print("NO DATABASE WRITES PERFORMED")
        return

    if args.confirm_project_ref != project_ref:
        raise ValueError(
            "SAFETY STOP: Production project confirmation required"
        )

    for start in range(0, len(records), 100):
        batch = records[start:start + 100]

        (
            client.table("app_matches")
            .upsert(
                batch,
                on_conflict=CONFLICT_COLUMNS,
            )
            .execute()
        )

        print(
            f"Uploaded {min(start + 100, len(records))}"
            f"/{len(records)}"
        )

    for (season, league), expected in EXPECTED.items():
        actual = row_count(
            client,
            league=league,
            season=season,
        )

        if actual != expected:
            raise ValueError(
                f"Verification failed: {league} {season}"
            )

    epl_after = row_count(client, league="PL")
    total_after = row_count(client)

    if total_after - epl_after != len(records):
        raise ValueError(
            "Unexpected non-EPL record count after upload"
        )

    if epl_after < epl_before:
        raise ValueError("EPL record count decreased")

    print("\nPRODUCTION UPLOAD: PASSED")
    print("EPL records:", epl_after)
    print("Other league records:", total_after - epl_after)
    print("Total records:", total_after)


if __name__ == "__main__":
    main()
