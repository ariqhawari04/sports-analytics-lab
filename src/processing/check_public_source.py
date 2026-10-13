
from datetime import date
import requests

SEASONS = ["2024-25", "2025-26", "2026-27"]

BASE_URL = (
    "https://raw.githubusercontent.com/"
    "openfootball/football.json/master"
)


def get_final_score(match):
    score = match.get("score")
    match_date = date.fromisoformat(match["date"])

    # Ignore future fixtures
    if match_date > date.today():
        return None

    if isinstance(score, dict):
        result = score.get("ft")
    elif isinstance(score, list):
        result = score
    else:
        return None

    if (
        not isinstance(result, list)
        or len(result) != 2
        or not all(isinstance(x, int) for x in result)
    ):
        return None

    return result


for season in SEASONS:
    url = f"{BASE_URL}/{season}/en.1.json"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    matches = response.json()["matches"]

    completed = [
        m for m in matches
        if get_final_score(m) is not None
    ]

    mu_points = 0
    mu_played = 0

    for match in completed:
        home, away = get_final_score(match)

        if "Manchester United" in match["team1"]:
            goals_for, goals_against = home, away
        elif "Manchester United" in match["team2"]:
            goals_for, goals_against = away, home
        else:
            continue

        mu_played += 1

        if goals_for > goals_against:
            mu_points += 3
        elif goals_for == goals_against:
            mu_points += 1

    latest_date = (
        max(m["date"] for m in completed)
        if completed else "N/A"
    )

    array_scores = sum(
        isinstance(m.get("score"), list)
        for m in completed
    )

    print(f"\n=== {season} ===")
    print(f"Fixtures: {len(matches)}")
    print(f"Matches with results: {len(completed)}")
    print(f"Latest result: {latest_date}")
    print(f"Array-format scores: {array_scores}")
    print(f"Manchester United played: {mu_played}")
    print(f"Manchester United points: {mu_points}")
