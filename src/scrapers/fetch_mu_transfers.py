import json
import time
from pathlib import Path

import pandas as pd

from src.scrapers.transfermarkt import get_player_transfers

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw"
PROCESSED = ROOT / "data/processed"

SQUAD_PATH = RAW / "transfermarkt_manchester_united_2024_2025.json"
CANDIDATES_PATH = PROCESSED / "manchester_united_player_candidates.csv"


def main():
    # 1. IDs from Transfermarkt historical squad
    with open(SQUAD_PATH, encoding="utf-8") as f:
        squad = json.load(f)

    squad_ids = {
        str(p["id"]) for p in squad["players"]
    }

    # 2. Additional candidates found through FBref
    candidates = pd.read_csv(
        CANDIDATES_PATH,
        dtype={"tm_id_candidate": str}
    )

    candidate_ids = set(
        candidates["tm_id_candidate"].dropna()
    )

    # Remove duplicates
    all_ids = sorted(squad_ids | candidate_ids)

    print(f"Total unique candidate IDs: {len(all_ids)}")

    success = 0
    cached = 0
    failed = []

    for i, player_id in enumerate(all_ids, start=1):
        path = (
            RAW /
            f"transfermarkt_player_{player_id}_transfers.json"
        )

        if path.exists():
            cached += 1
            print(f"[{i}/{len(all_ids)}] Cached: {player_id}")
            continue

        print(f"[{i}/{len(all_ids)}] Fetching: {player_id}")

        try:
            data = get_player_transfers(player_id)

            if not isinstance(data.get("transfers"), list):
                raise ValueError("Unexpected transfer response")

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            success += 1
            time.sleep(3)

        except Exception as exc:
            print(f"Failed: {player_id} - {exc}")
            failed.append(player_id)

            if "429" in str(exc):
                print("Rate limited. Stopping this run.")
                break

    print("\n--- SUMMARY ---")
    print(f"Cached: {cached}")
    print(f"Newly downloaded: {success}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("Failed IDs:", failed)


if __name__ == "__main__":
    main()
