import soccerdata as sd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"


def get_fbref_client(season="2024-25"):
    return sd.FBref(
        leagues="ENG-Premier League",
        seasons=season
    )


def get_fbref_schedule(season="2024-25"):
    fbref = get_fbref_client(season)
    return fbref.read_schedule()


def get_fbref_players(season="2024-25"):
    fbref = get_fbref_client(season)
    return fbref.read_player_season_stats(
        stat_type="standard"
    )


def save_fbref_schedule(season):
    matches = get_fbref_schedule(season)

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    season_label = season.replace("-", "_")
    output_path = (
        RAW_DIR / f"fbref_schedule_{season_label}.csv"
    )

    matches.to_csv(output_path)

    print(f"\nSeason: {season}")
    print(f"Rows: {len(matches)}")
    print(f"Saved to: {output_path}")

    if "score" in matches.columns:
        print(
            "Matches with scores:",
            matches["score"].notna().sum()
        )

    return matches


if __name__ == "__main__":
    for season in ["2025-26", "2026-27"]:
        save_fbref_schedule(season)