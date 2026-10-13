import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

file_path = (
    ROOT / "data/raw/"
    "transfermarkt_manchester_united_2024_2025.json"
)

with open(file_path, encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data["players"])

print(f"Total players: {len(df)}")
print(f"Unique player IDs: {df['id'].nunique()}")
print(f"Duplicate IDs: {df['id'].duplicated().sum()}")

print("\nPlayers:")
print(
    df[["id", "name", "position", "joinedOn"]]
    .to_string(index=False)
)
