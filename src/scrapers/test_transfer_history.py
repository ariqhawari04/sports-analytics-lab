
import json
from pathlib import Path

from transfermarkt import get_player_transfers

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "data" / "raw"

PLAYER_ID = "476701"  # Manuel Ugarte

def main():
    print(f"Fetching transfer history: {PLAYER_ID}")

    data = get_player_transfers(PLAYER_ID)

    output_path = (
        OUTPUT_DIR /
        f"transfermarkt_player_{PLAYER_ID}_transfers.json"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved: {output_path}")
    print("Response keys:", list(data.keys()))
    print(json.dumps(data, indent=2)[:4000])


if __name__ == "__main__":
    main()

