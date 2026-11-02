
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

BASE_URL = (
    "https://raw.githubusercontent.com/"
    "openfootball/football.json/master"
)

COLUMNS = [
    "source", "season", "game_id",
    "date", "time", "week",
    "home_team", "away_team",
    "home_goals", "away_goals", "score",
]

HISTORICAL_SEASONS = ["2024-25", "2025-26"]


LEAGUE_FILES = {
    "PL": "en.1",
    "BL1": "de.1",
    "PD": "es.1",
    "SA": "it.1",
    "FL1": "fr.1",
}


def extract_score(value):
    if isinstance(value, dict):
        value = value.get("ft")

    if (
        not isinstance(value, list)
        or len(value) != 2
        or not all(type(x) is int for x in value)
    ):
        raise ValueError(f"Unexpected score: {value}")

    return value[0], value[1]


def load_openfootball(season, league_code="PL"):
    if league_code not in LEAGUE_FILES:
        raise ValueError(
            f"Unsupported league code: {league_code}"
        )

    filename = LEAGUE_FILES[league_code]
    url = f"{BASE_URL}/{season}/{filename}.json"


    response = requests.get(url, timeout=30)
    response.raise_for_status()

    fixtures = response.json()["matches"]
    records = []

    for match in fixtures:
        home, away = extract_score(match["score"])

        records.append({
            "source": "openfootball",
            "season": season,
            "game_id": None,
            "date": match["date"],
            "time": match.get("time"),
            "week": int(
                match["round"].replace("Matchday ", "")
            ),
            "home_team": match["team1"],
            "away_team": match["team2"],
            "home_goals": home,
            "away_goals": away,
            "score": f"{home}-{away}",
        })

    return pd.DataFrame(records, columns=COLUMNS)


def load_football_data():
    path = PROCESSED / "football_data_2026_27.csv"

    df = pd.read_csv(path)

    # Reconstruct ASCII scores from numeric columns
    df["score"] = (
        df["home_goals"].astype(int).astype(str)
        + "-"
        + df["away_goals"].astype(int).astype(str)
    )

    return df[COLUMNS].copy()


def validate_season(df, season):
    expected = 380 if season != "2026-27" else None

    if expected and len(df) != expected:
        raise ValueError(
            f"{season}: expected 380, got {len(df)}"
        )

    teams = set(df["home_team"]) | set(df["away_team"])

    if len(teams) != 20:
        raise ValueError(
            f"{season}: expected 20 teams, got {len(teams)}"
        )

    duplicate = df.duplicated(
        ["season", "home_team", "away_team"]
    )

    if duplicate.any():
        raise ValueError(
            f"{season}: duplicate home-away fixture"
        )

    if df[["home_goals", "away_goals"]].isna().any().any():
        raise ValueError(
            f"{season}: missing final scores"
        )

    mu = df[
        (df["home_team"] == "Manchester United FC")
        | (df["away_team"] == "Manchester United FC")
    ]

    mu_points = 0

    for _, match in mu.iterrows():
        home = int(match["home_goals"])
        away = int(match["away_goals"])

        if match["home_team"] == "Manchester United FC":
            gf, ga = home, away
        else:
            gf, ga = away, home

        mu_points += 3 if gf > ga else 1 if gf == ga else 0

    print(
        f"{season}: {len(df)} matches, "
        f"{len(teams)} teams, "
        f"MU {len(mu)} matches / {mu_points} points"
    )

    expected_mu_points = {
        "2024-25": 42,
        "2025-26": 71,
    }

    if season in expected_mu_points:
        if len(mu) != 38:
            raise ValueError(
                f"{season}: MU did not play 38 matches"
            )

        if mu_points != expected_mu_points[season]:
            raise ValueError(
                f"{season}: MU points mismatch"
            )


def main():
    frames = []

    for season in HISTORICAL_SEASONS:
        df = load_openfootball(season)
        validate_season(df, season)
        frames.append(df)

    current = load_football_data()
    validate_season(current, "2026-27")
    frames.append(current)

    combined = pd.concat(
        frames,
        ignore_index=True
    )

    combined = combined.sort_values(
        ["season", "date", "week", "home_team"]
    ).reset_index(drop=True)

    PROCESSED.mkdir(
        parents=True,
        exist_ok=True
    )

    output = PROCESSED / "salt_epl_matches.csv"
    combined.to_csv(output, index=False, encoding="utf-8-sig")

    print("\n=== SALT PUBLIC DATASET ===")
    print(combined.groupby("season").size())
    print("Total completed matches:", len(combined))
    print("Saved:", output)


if __name__ == "__main__":
    main()
