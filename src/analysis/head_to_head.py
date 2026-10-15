import pandas as pd


def get_head_to_head(matches, team_a, team_b, seasons=None):
    """
    Calculate head-to-head results between two clubs
    using completed matches in the available dataset.
    """

    if team_a == team_b:
        raise ValueError("Please select two different clubs.")

    data = matches.copy()

    if seasons is not None:
        data = data[data["season"].isin(seasons)]

    meetings = data[
        (
            (data["home_team"] == team_a)
            & (data["away_team"] == team_b)
        )
        |
        (
            (data["home_team"] == team_b)
            & (data["away_team"] == team_a)
        )
    ].copy()

    meetings = meetings.sort_values(
        ["match_date", "matchweek"],
        ascending=[False, False],
    )

    a_wins = 0
    b_wins = 0
    draws = 0

    for match in meetings.itertuples():

        if match.home_goals == match.away_goals:
            draws += 1
            continue

        winner = (
            match.home_team
            if match.home_goals > match.away_goals
            else match.away_team
        )

        if winner == team_a:
            a_wins += 1
        else:
            b_wins += 1

    summary = {
        "matches": len(meetings),
        "team_a_wins": a_wins,
        "draws": draws,
        "team_b_wins": b_wins,
    }

    return summary, meetings