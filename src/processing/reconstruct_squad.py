
import json
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"

MU_ID = "985"
CUTOFF = date(2024, 8, 31)


def get_club_at_date(transfer_data, cutoff):
    """Determine a player's club from their latest transfer."""
    transfers = transfer_data.get("transfers", [])

    eligible = [
        t for t in transfers
        if t.get("date")
        and date.fromisoformat(t["date"]) <= cutoff
        and t.get("clubTo")
        and t["clubTo"].get("id")
    ]

    if not eligible:
        return None

    latest = max(
        eligible,
        key=lambda t: t["date"]
    )

    return {
        "club_id": str(latest["clubTo"]["id"]),
        "club_name": latest["clubTo"]["name"],
        "last_transfer_date": latest["date"],
        "transfer_type": latest.get("transferType")
    }


if __name__ == "__main__":
    path = RAW_DIR / "transfermarkt_player_476701_transfers.json"

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    result = get_club_at_date(data, CUTOFF)

    print("Player ID:", data["id"])
    print("Cutoff:", CUTOFF)
    print("Club at cutoff:", result)
    print(
        "In Manchester United:",
        result is not None and result["club_id"] == MU_ID
    )
