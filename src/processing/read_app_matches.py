
import pandas as pd
import psycopg
from psycopg.rows import dict_row


def fetch_app_matches(host, user, password):
    """
    Read match data using a restricted
    PostgreSQL account.
    """

    with psycopg.connect(
        host=host,
        port=5432,
        dbname="postgres",
        user=user,
        password=password,
        sslmode="require",
        connect_timeout=15,
        row_factory=dict_row,
    ) as conn:

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    season,
                    source,
                    match_date,
                    matchweek,
                    home_team,
                    away_team,
                    home_goals,
                    away_goals
                FROM public.app_matches
                ORDER BY season, match_date, id
            """)

            records = cursor.fetchall()

    if not records:
        raise ValueError(
            "No matches returned from Supabase"
        )

    df = pd.DataFrame(records)

    # Validate fixture uniqueness
    if df.duplicated([
        "season",
        "home_team",
        "away_team",
    ]).any():
        raise ValueError(
            "Duplicate fixtures found"
        )

    # Prepare data for the analytics engine
    df["season_label"] = df["season"]

    df["match_date"] = pd.to_datetime(
        df["match_date"],
        errors="raise",
    )

    df["matchweek"] = pd.to_numeric(
        df["matchweek"],
        errors="raise",
    )

    for col in ["home_goals", "away_goals"]:
        df[col] = pd.to_numeric(
            df[col],
            errors="raise",
        )

    required = [
        "season",
        "match_date",
        "matchweek",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
    ]

    if df[required].isna().any().any():
        raise ValueError(
            "Incomplete match records"
        )

    return df
