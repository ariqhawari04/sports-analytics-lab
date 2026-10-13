import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["API_FOOTBALL_KEY"]
BASE_URL = "https://v3.football.api-sports.io"

headers = {
    "x-apisports-key": API_KEY
}

for season in [2022, 2024]:
    response = requests.get(
        f"{BASE_URL}/fixtures",
        headers=headers,
        params={"league": 39, "season": season},
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    print(f"\n=== EPL {season}/{str(season + 1)[-2:]} ===")
    print("API errors:", data.get("errors"))
    print("Results:", data.get("results"))
    print("Pagination:", data.get("paging"))
    print(
        "Remaining requests:",
        response.headers.get(
            "x-ratelimit-requests-remaining"
        ),
    )
