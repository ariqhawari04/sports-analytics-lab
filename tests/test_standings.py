
import pandas as pd

from src.analysis.standings import build_standings


def make_results(team, wins, draws, losses, season):
    rows = []

    for result, count in [
        ("W", wins),
        ("D", draws),
        ("L", losses),
    ]:
        for _ in range(count):
            gf, ga = {
                "W": (2, 0),
                "D": (1, 1),
                "L": (0, 2),
            }[result]

            rows.append({
                "season": season,
                "team": team,
                "result": result,
                "points": {"W": 3, "D": 1, "L": 0}[result],
                "goals_for": gf,
                "goals_against": ga,
            })

    return rows


rows = []

rows += make_results(
    "Everton FC", 13, 9, 16, "2023-24"
)
rows += make_results(
    "Nottingham Forest FC", 9, 9, 20, "2023-24"
)
rows += make_results(
    "Manchester United FC", 18, 6, 14, "2023-24"
)

results = pd.DataFrame(rows)

standings = build_standings(results).set_index("team")

# Official points after deductions
assert standings.loc["Everton FC", "Pts"] == 40
assert standings.loc["Everton FC", "Deduction"] == 8

assert standings.loc["Nottingham Forest FC", "Pts"] == 32
assert standings.loc["Nottingham Forest FC", "Deduction"] == 4

assert standings.loc["Manchester United FC", "Pts"] == 60
assert standings.loc["Manchester United FC", "Deduction"] == 0

# Match-earned points remain unchanged
earned = results.groupby("team")["points"].sum()

assert earned["Everton FC"] == 48
assert earned["Nottingham Forest FC"] == 36

# No deductions in another season
other = pd.DataFrame(
    make_results("Everton FC", 1, 0, 0, "2024-25")
)

other_table = build_standings(other)

assert other_table.iloc[0]["Pts"] == 3
assert other_table.iloc[0]["Deduction"] == 0

# Prevent accidental mixing of multiple seasons
try:
    build_standings(pd.concat([results, other]))
except ValueError:
    pass
else:
    raise AssertionError(
        "Mixed seasons should raise ValueError"
    )

print("Official standings calculations passed!")
