
import json
import time
from pathlib import Path

import pandas as pd

from src.scrapers.transfermarkt import search_player

ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT / "data/processed/"
    "manchester_united_squad_comparison.csv"
)

OUTPUT = (
    ROOT / "data/processed/"
    "manchester_united_player_candidates.csv"
)

CACHE_DIR = ROOT / "data/raw/player_search"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def search_with_cache(player_name):
    cache_path = CACHE_DIR / (
        player_name.lower()
        .replace(" ", "_")
        .replace("/", "_") + ".json"
    )

    if cache_path.exists():
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    result = search_player(player_name)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    time.sleep(2)
    return result


def main():
    df = pd.read_csv(INPUT)

    unmatched = df.loc[
        df["status"] == "fbref_only",
        "player_name"
    ].dropna().unique()

    print(f"Unmatched players: {len(unmatched)}")

    candidate_rows = []

    for name in unmatched:
        print(f"\nSearching: {name}")

        try:
            data = search_with_cache(name)
            results = data.get("results", [])

            for candidate in results[:5]:
                club = candidate.get("club") or {}

                candidate_rows.append({
                    "fbref_name": name,
                    "tm_id_candidate": candidate.get("id"),
                    "tm_name_candidate": candidate.get("name"),
                    "tm_club_candidate": club.get("name"),
                    "match_status": "needs_validation"
                })

            if not results:
                candidate_rows.append({
                    "fbref_name": name,
                    "tm_id_candidate": None,
                    "tm_name_candidate": None,
                    "tm_club_candidate": None,
                    "match_status": "not_found"
                })

        except Exception as exc:
            print(f"Search failed for {name}: {exc}")

            candidate_rows.append({
                "fbref_name": name,
                "match_status": "search_error"
            })

    candidates = pd.DataFrame(candidate_rows)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(OUTPUT, index=False)

    print("\nSearch candidates:")
    print(candidates.to_string(index=False))

    print(f"\nSaved: {OUTPUT}")


if __name__ == "__main__":
    main()
