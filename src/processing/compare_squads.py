import json
from pathlib import Path
import unicodedata

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

FBREF_PATH = ROOT / "data/raw/fbref_players_2024_25.csv"

TM_PATH = (
    ROOT / "data/raw/"
    "transfermarkt_manchester_united_2024_2025.json"
)

OUTPUT_PATH = (
    ROOT / "data/processed/"
    "manchester_united_squad_comparison.csv"
)


def normalize_name(name):
    """Normalize names for initial comparison."""
    name = str(name).strip().casefold()

    name = "".join(
        char for char in unicodedata.normalize("NFKD", name)
        if not unicodedata.combining(char)
    )

    return " ".join(name.split())


def main():
    
    fbref = pd.read_csv(FBREF_PATH, header=[0, 1])

    # Flatten statistical columns while preserving index names
    flattened_columns = []

    for upper, lower in fbref.columns:
        if str(upper).startswith("Unnamed"):
            upper = ""

        if str(lower).startswith("Unnamed"):
            lower = ""

        column_name = " ".join(
            part for part in [str(upper), str(lower)]
            if part
        ).strip()

        flattened_columns.append(column_name)

    # Restore the original FBref MultiIndex row labels
    flattened_columns[:4] = [
        "league",
        "season",
        "team",
        "player"
    ]

    fbref.columns = flattened_columns

    print("FBref columns:", fbref.columns.tolist())


    print("FBref columns:", fbref.columns.tolist())

    # Filter Manchester United
    mu_fbref = fbref[
        fbref["team"] == "Manchester Utd"
    ].copy()

    mu_fbref = mu_fbref.rename(
        columns={"player": "player_name"}
    )

    # Read Transfermarkt historical squad
    with open(TM_PATH, encoding="utf-8") as f:
        tm_data = json.load(f)

    tm = pd.DataFrame(tm_data["players"])

    tm = tm.rename(
        columns={
            "id": "transfermarkt_id",
            "name": "player_name"
        }
    )

    # Name matching (initial version)
    mu_fbref["name_key"] = (
        mu_fbref["player_name"].apply(normalize_name)
    )

    tm["name_key"] = (
        tm["player_name"].apply(normalize_name)
    )

    # Compare union of players
    comparison = mu_fbref[
        ["player_name", "name_key", "Playing Time MP"]
    ].merge(
        tm[
            [
                "name_key",
                "transfermarkt_id",
                "joinedOn"
            ]
        ],
        on="name_key",
        how="outer",
        indicator=True
    )

    comparison["status"] = comparison["_merge"].map({
        "both": "matched",
        "left_only": "fbref_only",
        "right_only": "transfermarkt_only"
    })

    comparison = comparison.drop(
        columns=["name_key", "_merge"]
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    comparison.to_csv(OUTPUT_PATH, index=False)

    print("\nComparison summary:")
    print(comparison["status"].value_counts())

    print("\nFBref players missing from TM API:")
    print(
        comparison[
            comparison["status"] == "fbref_only"
        ].to_string(index=False)
    )

    print(f"\nSaved comparison to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
