
import json
from pathlib import Path
from datetime import date

from src.scrapers.transfermarkt import get_player_transfers
from src.processing.reconstruct_squad import get_club_at_date

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"

PLAYERS = {
    "Manuel Ugarte": "476701",
    "Marcus Rashford": "258923",
    "Scott McTominay": "315969",
}

CUTOFFS = [
    date(2024, 8, 31),
    date(2025, 2, 4),
]


def load_transfer_history(player_id):
    """Use locally saved data before requesting the API."""
    path = (
        RAW_DIR /
        f"transfermarkt_player_{player_id}_transfers.json"
    )

    if path.exists():
        print(f"Using cached transfer history: {player_id}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    print(f"Fetching transfer history: {player_id}")
    data = get_player_transfers(player_id)

    if not isinstance(data.get("transfers"), list):
        raise ValueError("Unexpected transfer response")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return data


def main():
    for player_name, player_id in PLAYERS.items():
        print(f"\n{'=' * 45}")
        print(f"PLAYER: {player_name}")

        data = load_transfer_history(player_id)

        for cutoff in CUTOFFS:
            result = get_club_at_date(data, cutoff)

            club = (
                result["club_name"]
                if result is not None
                else "Unknown"
            )

            print(f"{cutoff}: {club}")


if __name__ == "__main__":
    main()
