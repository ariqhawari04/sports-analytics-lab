
import json
import time
from pathlib import Path

import requests
from requests.exceptions import RequestException

BASE_URL = "https://transfermarkt-api.fly.dev"

CLUB_ID = 985
CLUB_NAME = "manchester_united"
SEASON = 2024

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def fetch_json(endpoint, params=None):
    """Fetch JSON with limited retries and clear errors."""
    url = f"{BASE_URL}{endpoint}"

    for attempt in range(1, 4):
        try:
            response = requests.get(
                url,
                params=params,
                timeout=(10, 60)
            )

            print(f"HTTP Status: {response.status_code}")

            # Avoid repeatedly retrying rate limits
            if response.status_code == 429:
                response.raise_for_status()

            response.raise_for_status()
            return response.json()

        except (requests.Timeout, requests.ConnectionError):
            if attempt == 3:
                raise

            print(f"Connection issue. Retry {attempt}/2...")
            time.sleep(5 * attempt)

        except requests.HTTPError as exc:
            status = exc.response.status_code

            if status not in (502, 503, 504) or attempt == 3:
                raise

            print(f"Server error {status}. Retry {attempt}/2...")
            time.sleep(5 * attempt)

    raise RequestException("Request failed")


def get_club_players(club_id, season):
    return fetch_json(
        f"/clubs/{club_id}/players",
        params={"season_id": season}
    )


def get_player_market_value(player_id):
    return fetch_json(
        f"/players/{player_id}/market_value"
    )

def get_player_transfers(player_id):
    return fetch_json(
        f"/players/{player_id}/transfers"
    )

def search_player(player_name):
    return fetch_json(
        f"/players/search/{requests.utils.quote(player_name, safe='')}"
    )

def get_player_profile(player_id):
    return fetch_json(
        f"/players/{player_id}/profile"
    )

def load_or_fetch_squad(club_id, club_name, season):
    """Reuse saved JSON whenever possible."""
    path = (
        RAW_DIR /
        f"transfermarkt_{club_name}_{season}_{season + 1}.json"
    )

    if path.exists():
        print(f"Loading cached file: {path.name}")

        with open(path, encoding="utf-8") as f:
            return json.load(f)

    print(f"Fetching {club_name} {season}/{season + 1}...")

    data = get_club_players(club_id, season)

    if not isinstance(data, dict) or not isinstance(
        data.get("players"), list
    ):
        raise ValueError("Unexpected squad response structure")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved: {path.name}")
    return data


if __name__ == "__main__":
    squad = load_or_fetch_squad(
        CLUB_ID,
        CLUB_NAME,
        SEASON
    )

    print(f"Players returned: {len(squad['players'])}")
    print(f"Unique IDs: {len(set(p['id'] for p in squad['players']))}")
