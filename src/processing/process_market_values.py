
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = (
    ROOT / "data/raw/transfermarkt_player_262749_values.json"
)

OUTPUT_PATH = (
    ROOT / "data/processed/david_raya_market_values.csv"
)

CUTOFF_DATE = pd.Timestamp("2024-08-31")


def main():
    with open(INPUT_PATH, encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data["marketValueHistory"])

    # Store the player's Transfermarkt ID
    df["player_id"] = str(data["id"])

    # Convert dates and values to proper types
    df["date"] = pd.to_datetime(df["date"])
    df["marketValue"] = pd.to_numeric(
        df["marketValue"],
        errors="coerce"
    )

    # Clean and standardize column names
    df = df.rename(columns={
        "date": "valuation_date",
        "marketValue": "market_value_eur",
        "clubId": "club_id",
        "clubName": "club_name"
    })

    df = df[
        [
            "player_id",
            "valuation_date",
            "club_id",
            "club_name",
            "market_value_eur"
        ]
    ].sort_values("valuation_date")

    # Save full history, not just one snapshot
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    # Get latest known value at or before cutoff
    eligible = df[
        (df["valuation_date"] <= CUTOFF_DATE)
        & df["market_value_eur"].notna()
    ]

    if eligible.empty:
        print("No historical valuation before cutoff")
        return

    snapshot = eligible.iloc[-1]

    print("\nHistorical valuation snapshot")
    print(f"Player ID: {snapshot['player_id']}")
    print(f"Cutoff: {CUTOFF_DATE.date()}")
    print(f"Valuation date: {snapshot['valuation_date'].date()}")
    print(f"Club at valuation: {snapshot['club_name']}")
    print(f"Market value: EUR {snapshot['market_value_eur']:,.0f}")

    print(f"\nSaved full history to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
