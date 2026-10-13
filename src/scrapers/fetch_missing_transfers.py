from pathlib import Path
import json
import time

from src.scrapers.transfermarkt import get_player_transfers

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data/raw"

PLAYER_IDS = [
    "602105",   # Antony
    "1042886",  # Chido Obi
    "258923",   # Rashford
    "315969",   # McTominay
    "911424",   # Fredricson
    "339340",   # Malacia
]

for player_id in PLAYER_IDS:
    path = (
        RAW_DIR /
        f"transfermarkt_player_{player_id}_transfers.json"
    )

    if path.exists():
        print(f"Cached: {player_id}")
        continue

    print(f"Fetching: {player_id}")

    try:
        data = get_player_transfers(player_id)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        time.sleep(2)

    except Exception as exc:
        print(f"Failed: {player_id} — {exc}")