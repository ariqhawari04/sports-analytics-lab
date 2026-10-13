
import pandas as pd
from supabase import create_client


def fetch_app_matches(url, secret_key):
    """
    Fetch all completed matches from Supabase
    using pagination.
    """

    client = create_client(url, secret_key)

    records = []
    page_size = 500
    offset = 0

    columns = (
        "id,season,source,match_date,matchweek,"
        "home_team,away_team,home_goals,away_goals"
    )

    while True:
        response = (
            client.table("app_matches")
            .select(columns)
            .order("id")
            .range(offset, offset + page_size - 1)
            .execute()
        )

        batch = response.data or []
        records.extend(batch)

        if len(batch) < page_size:
            break

        offset += page_size

    if not records:
        raise ValueError(
            "No matches returned from Supabase"
        )

    df = pd.DataFrame(records)

    # Validate fixture uniqueness
    if df.duplicated(
        ["season", "home_team", "away_team"]
    ).any():
        raise ValueError("Duplicate fixtures found")

    # Convert database columns to analytics format
    df["season_label"] = df["season"]

    df["match_date"] = pd.to_datetime(
        df["match_date"],
        errors="raise"
    )

    df["matchweek"] = pd.to_numeric(
        df["matchweek"],
        errors="raise"
    )

    for col in ["home_goals", "away_goals"]:
        df[col] = pd.to_numeric(
            df[col],
            errors="raise"
        )

    required = [
        "season", "match_date", "matchweek",
        "home_team", "away_team",
        "home_goals", "away_goals"
    ]

    if df[required].isna().any().any():
        raise ValueError("Incomplete match records")

    return df
