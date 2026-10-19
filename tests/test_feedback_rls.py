import streamlit as st
from supabase import create_client
from postgrest.exceptions import APIError


def main():
    client = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_PUBLISHABLE_KEY"],
    )

    print("Testing anonymous SELECT access...")

    try:
        response = (
            client.table("product_feedback")
            .select("id")
            .limit(1)
            .execute()
        )

        if response.data:
            raise SystemExit(
                "FAIL: Anonymous users can read feedback!"
            )

        print("PASS: No feedback rows visible to anon.")

    except APIError as error:
        if str(error.code) == "42501":
            print("PASS: SELECT permission denied (42501).")
        else:
            raise RuntimeError(
                f"Unexpected API error: {error.code}"
            ) from error


if __name__ == "__main__":
    main()
