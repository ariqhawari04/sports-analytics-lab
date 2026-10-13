
import json
from pathlib import Path

from transfermarkt import get_club_players

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"

OLD_PATH = (
    RAW_DIR / "transfermarkt_manchester_united_2024_2025.json"
)

NEW_PATH = (
    RAW_DIR / "transfermarkt_manchester_united_2024_2025_retest.json"
)

CLUB_ID = 985
SEASON = 2024


def main():
    with open(OLD_PATH, encoding="utf-8") as f:
        old_data = json.load(f)

    print(f"Original players: {len(old_data['players'])}")

    # Fetch again, ignoring local cached JSON
    print("\nFetching fresh squad response...")
    new_data = get_club_players(CLUB_ID, SEASON)

    if not isinstance(new_data.get("players"), list):
        raise ValueError("Unexpected API response")

    print(f"New players: {len(new_data['players'])}")

    with open(NEW_PATH, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    old_ids = {str(p["id"]) for p in old_data["players"]}
    new_ids = {str(p["id"]) for p in new_data["players"]}

    print("\nNEW PLAYERS:")
    for player in new_data["players"]:
        if str(player["id"]) not in old_ids:
            print(player["name"], player["id"])

    print("\nMISSING FROM NEW RESPONSE:")
    for player in old_data["players"]:
        if str(player["id"]) not in new_ids:
            print(player["name"], player["id"])

    print(f"\nSaved retest response: {NEW_PATH.name}")


if __name__ == "__main__":
    main()
