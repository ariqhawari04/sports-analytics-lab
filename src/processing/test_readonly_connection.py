
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


with psycopg.connect(
    host=os.environ["SUPABASE_POOLER_HOST"],
    port=5432,
    dbname="postgres",
    user=os.environ["SUPABASE_READER_USER"],
    password=os.environ["SUPABASE_READER_PASSWORD"],
    sslmode="require",
    connect_timeout=15,
) as conn:

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                current_user,
                COUNT(*) AS total_matches,
                has_table_privilege(
                    current_user,
                    'public.app_matches',
                    'INSERT'
                ) AS can_insert,
                has_table_privilege(
                    current_user,
                    'public.app_matches',
                    'UPDATE'
                ) AS can_update,
                has_table_privilege(
                    current_user,
                    'public.app_matches',
                    'DELETE'
                ) AS can_delete
            FROM public.app_matches
        """)

        role, total, can_insert, can_update, can_delete = (
            cur.fetchone()
        )

        print("Connected as:", role)
        print("Total matches:", total)
        print("Can INSERT:", can_insert)
        print("Can UPDATE:", can_update)
        print("Can DELETE:", can_delete)

        assert role == "sports_app_reader"
        assert total >= 820
        assert not any([
            can_insert,
            can_update,
            can_delete,
        ])

        print("\nREAD-ONLY CONNECTION SUCCESSFUL!")

