
import pandas as pd
import psycopg
from psycopg.rows import dict_row


def fetch_app_matches(host, user, password, league_code=None):
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
            query = """
                SELECT
                    COALESCE(
                        to_jsonb(m)->>'league_code',
                        'PL'
                    ) AS league_code,
                    m.season,
                    m.source,
                    m.match_date,
                    m.matchweek,
                    m.home_team,
                    m.away_team,
                    m.home_goals,
                    m.away_goals
                FROM public.app_matches AS m
            """

            params = ()

            if league_code == "PL":
                # Compatible with old EPL schema.
                query += """
                    WHERE COALESCE(
                        to_jsonb(m)->>'league_code',
                        'PL'
                    ) = %s
                """
                params = ("PL",)

            elif league_code in {"BL1", "PD", "SA", "FL1"}:
                # Uses the indexed league_code column.
                query += """
                    WHERE m.league_code = %s
                """
                params = (league_code,)

            elif league_code is not None:
                raise ValueError(
                    f"Unsupported league: {league_code}"
                )

            query += """
                ORDER BY
                    m.season,
                    m.match_date,
                    m.id
            """

            cursor.execute(query, params)
            records = cursor.fetchall()


    if not records:
        raise ValueError(
            "No matches returned from Supabase"
        )

    df = pd.DataFrame(records)

    # Validate fixture uniqueness
    if df.duplicated([
        "league_code",
        "season",
        "home_team",
        "away_team",
        "match_date",
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
        "league_code",
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
