import os
from pathlib import Path

import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

API_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

if not API_TOKEN:
    raise RuntimeError(
        "FOOTBALL_DATA_TOKEN not found in .env"
    )

URL = (
    "https://api.football-data.org"
    "/v4/competitions/PL/matches"
)

response = requests.get(
    URL,
    headers={"X-Auth-Token": API_TOKEN},
    timeout=30,
)

print("HTTP status:", response.status_code)

if response.status_code != 200:
    print("API error:", response.text[:500])
    response.raise_for_status()

data = response.json()
matches = data.get("matches", [])

completed = [
    m for m in matches
    if m.get("status") == "FINISHED"
    and m.get("score", {}).get("fullTime", {}).get("home")
        is not None
    and m.get("score", {}).get("fullTime", {}).get("away")
        is not None
]

season_info = data.get("competition", {})

print("\n=== FOOTBALL-DATA.ORG AUDIT ===")
print("Competition:", season_info.get("name"))
print("Total fixtures:", len(matches))
print("Completed matches:", len(completed))
print("Other statuses:", len(matches) - len(completed))

if completed:
    latest = max(
        m["utcDate"] for m in completed
    )
    print("Latest completed match:", latest)

print("\n=== SAMPLE COMPLETED MATCH ===")

if completed:
    sample = completed[-1]

    print("Match ID:", sample.get("id"))
    print("Date:", sample.get("utcDate"))
    print("Matchday:", sample.get("matchday"))
    print("Status:", sample.get("status"))
    print(
        "Home:",
        sample.get("homeTeam", {}).get("name")
    )
    print(
        "Away:",
        sample.get("awayTeam", {}).get("name")
    )
    print(
        "Score:",
        sample.get("score", {}).get("fullTime")
    )

print("\nNo data has been uploaded or modified.")



# ==========================================
# TEAM NAME AUDIT
# ==========================================

teams = {}

for match in matches:
    for side in ["homeTeam", "awayTeam"]:
        team = match[side]

        if team.get("id") is not None:
            teams[team["id"]] = {
                "name": team.get("name"),
                "short_name": team.get("shortName"),
                "tla": team.get("tla"),
            }

print("\n=== TEAM NAME AUDIT ===")
print("Unique teams:", len(teams))

for team_id, info in sorted(
    teams.items(),
    key=lambda x: x[1]["name"] or ""
):
    print(
        team_id,
        "|", info["name"],
        "|", info["short_name"],
        "|", info["tla"],
    )
