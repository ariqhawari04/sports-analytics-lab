
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "data" / "processed"

load_dotenv(ROOT / ".env")

API_KEY = os.environ["FOOTBALL_DATA_TOKEN"]

URL = (
    "https://api.football-data.org"
    "/v4/competitions/PL/matches"
)

SEASON = 2026


def export_matches():
    response = requests.get(
        URL,
        headers={"X-Auth-Token": API_KEY},
        params={"season": SEASON},
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()
    fixtures = data["matches"]

    # Validate the response before processing
    if len(fixtures) != 380:
        raise ValueError(
            f"Expected 380 fixtures, got {len(fixtures)}"
        )

    fixture_ids = [m["id"] for m in fixtures]

    if len(fixture_ids) != len(set(fixture_ids)):
        raise ValueError("Duplicate match IDs found")

    # Check team identities across all fixtures
    teams = {}

    for match in fixtures:
        for side in ["homeTeam", "awayTeam"]:
            team = match[side]
            team_id = team["id"]
            team_name = team["name"]

            if team_id is None or not team_name:
                raise ValueError("Missing team identity")

            if (
                team_id in teams
                and teams[team_id] != team_name
            ):
                raise ValueError(
                    f"Inconsistent name for team {team_id}"
                )

            teams[team_id] = team_name

    if len(teams) != 20:
        raise ValueError(
            f"Expected 20 clubs, found {len(teams)}"
        )

    records = []
    retrieved_at = datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")

    for match in fixtures:
        if match["status"] != "FINISHED":
            continue

        score = match["score"]["fullTime"]

        home_goals = score["home"]
        away_goals = score["away"]

        if home_goals is None or away_goals is None:
            raise ValueError(
                f"Missing final score: {match['id']}"
            )

        records.append({
            "source": "football-data.org",
            "season": "2026-27",
            "game_id": match["id"],
            "date": match["utcDate"][:10],
            "time": match["utcDate"][11:16],
            "week": match["matchday"],
            "home_team_id": match["homeTeam"]["id"],
            "away_team_id": match["awayTeam"]["id"],
            "home_team": match["homeTeam"]["name"],
            "away_team": match["awayTeam"]["name"],
            "home_goals": home_goals,
            "away_goals": away_goals,
            "score": f"{home_goals}–{away_goals}",
            "retrieved_at_utc": retrieved_at,
        })

    if not records:
        raise ValueError("No completed matches found")

    df = pd.DataFrame(records)

    df = df.sort_values(
        ["date", "game_id"]
    ).reset_index(drop=True)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        OUTPUT_DIR / "football_data_2026_27.csv"
    )

    df.to_csv(output_path, index=False)

    print("\n=== SALT DATA EXPORT ===")
    print("Source: football-data.org")
    print("Season: 2026/27")
    print("Total fixtures:", len(fixtures))
    print("Unique clubs:", len(teams))
    print("Completed matches:", len(df))
    print("Latest result:", df["date"].max())
    print("Unique match IDs:", df["game_id"].nunique())
    print("Saved to:", output_path)

    print("\nSample:")
    print(df[[
        "date",
        "home_team",
        "away_team",
        "score",
    ]].tail())


if __name__ == "__main__":
    export_matches()
