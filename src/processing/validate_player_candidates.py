
import json
import time
from pathlib import Path

from src.scrapers.transfermarkt import get_player_profile

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "data/raw/player_profiles"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Candidate IDs discovered automatically by our search
CANDIDATES = {
    "Antony": "602105",
    "Chidozie Obi-Martin": "1042886",
    "Marcus Rashford": "258923",
    "Scott McTominay": "315969",
    "Tyler Fredricson": "911424",
    "Tyrell Malacia": "339340",
}


def main():
    for name, player_id in CANDIDATES.items():
        path = CACHE_DIR / f"{player_id}.json"

        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        else:
            print(f"Fetching profile: {name}")
            data = get_player_profile(player_id)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    indent=2,
                    ensure_ascii=False
                )

            time.sleep(2)

        print(f"\nFBref: {name}")
        print(f"Transfermarkt ID: {player_id}")
        print("Profile fields:", list(data.keys()))

        # Inspect fields before building validation rules
        print(json.dumps(data, indent=2, ensure_ascii=False)[:900])


if __name__ == "__main__":
    main()
