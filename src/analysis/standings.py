
"""
Premier League standings calculations.

Official points deductions are applied to league
standings, not to points earned from match results.
"""

POINT_DEDUCTIONS = {
    "2023-24": {
        "Everton FC": 8,
        "Nottingham Forest FC": 4,
    },
}


def build_standings(results):
    if results.empty:
        raise ValueError("Cannot build empty standings.")

    seasons = results["season"].unique()

    if len(seasons) != 1:
        raise ValueError(
            "Standings must contain exactly one season."
        )

    season = seasons[0]


    # Prevent standings from mixing different leagues.
    if "league_code" in results.columns:
        if results["league_code"].isna().any():
            raise ValueError(
                "Missing league_code in standings data."
            )

        leagues = results["league_code"].unique()

        if len(leagues) != 1:
            raise ValueError(
                "Standings must contain exactly one league."
            )

        league_code = leagues[0]
    else:
        # Backward compatibility with the existing
        # EPL-only Streamlit application.
        league_code = "PL"


    table = (
        results.groupby("team")
        .agg(
            MP=("points", "size"),
            W=("result", lambda x: (x == "W").sum()),
            D=("result", lambda x: (x == "D").sum()),
            L=("result", lambda x: (x == "L").sum()),
            GF=("goals_for", "sum"),
            GA=("goals_against", "sum"),
            Pts=("points", "sum"),
        )
        .reset_index()
    )

    table["GD"] = table["GF"] - table["GA"]

    deductions = (
        POINT_DEDUCTIONS.get(season, {})
        if league_code == "PL"
        else {}
    )

    table["Deduction"] = (
        table["team"]
        .map(deductions)
        .fillna(0)
        .astype(int)
    )

    table["Pts"] -= table["Deduction"]

    table = table.sort_values(
        ["Pts", "GD", "GF"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    table.insert(0, "Position", table.index + 1)

    return table
