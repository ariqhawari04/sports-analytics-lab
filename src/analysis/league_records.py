"""Season-level league and club records from completed football matches."""

import pandas as pd


def _longest_streak(results, accepted):
    """Find the longest uninterrupted run of accepted W/D/L results."""
    longest = current = 0
    for result in results:
        current = current + 1 if result in accepted else 0
        longest = max(longest, current)
    return longest


def get_longest_streak_runs(
    all_results,
    season,
    team,
    streak_type="winning",
):
    """
    Return all longest streaks for a club in one season.

    winning: consecutive W results
    unbeaten: consecutive W or D results

    Each longest streak is returned as a DataFrame
    of its contributing matches in chronological order.
    """

    allowed_by_type = {
        "winning": {"W"},
        "unbeaten": {"W", "D"},
    }

    if streak_type not in allowed_by_type:
        raise ValueError(
            "streak_type must be 'winning' or 'unbeaten'"
        )

    allowed_results = allowed_by_type[streak_type]

    games = (
        all_results.loc[
            (all_results["season"] == season)
            & (all_results["team"] == team)
        ]
        .sort_values("match_number")
        .reset_index(drop=True)
    )

    best_length = _longest_streak(
        games["result"],
        allowed_results,
    )

    if best_length == 0:
        return []

    longest_runs = []
    run_start = None

    for index, result in enumerate(games["result"]):

        if result in allowed_results:
            if run_start is None:
                run_start = index

        elif run_start is not None:

            if index - run_start == best_length:
                longest_runs.append(
                    games.iloc[run_start:index].copy()
                )

            run_start = None

    # Handle a streak continuing through
    # the club's latest completed match.
    if run_start is not None:

        if len(games) - run_start == best_length:
            longest_runs.append(
                games.iloc[run_start:].copy()
            )

    return longest_runs


def build_club_records(all_results, season):
    """One record per club in a season, using chronological match order."""
    season_data = all_results.loc[
        all_results["season"] == season
    ].sort_values(["team", "match_number"])
    if season_data.empty:
        raise ValueError(f"No completed matches for season {season}")

    rows = []
    for club, games in season_data.groupby("team", sort=True):
        home = games.loc[games["location"] == "Home"]
        away = games.loc[games["location"] == "Away"]
        points = int(games["points"].sum())
        home_points = int(home["points"].sum())
        away_points = int(away["points"].sum())
        rows.append({
            "team": club,
            "MP": len(games),
            "Pts": points,
            "Clean_Sheets": int((games["goals_against"] == 0).sum()),
            "Longest_Winning_Streak": _longest_streak(games["result"], {"W"}),
            "Longest_Unbeaten_Streak": _longest_streak(games["result"], {"W", "D"}),
            "Home_MP": len(home),
            "Home_Pts": home_points,
            "Home_PPG": home_points / len(home) if len(home) else float("nan"),
            "Away_MP": len(away),
            "Away_Pts": away_points,
            "Away_PPG": away_points / len(away) if len(away) else float("nan"),
        })
    return pd.DataFrame(rows)


def get_match_extremes(matches, season):
    """Highest total goals and largest winning margin; preserve all ties."""
    season_data = matches.loc[
        matches["season"] == season
    ].copy()
    if season_data.empty:
        raise ValueError(f"No completed matches for season {season}")

    season_data["Total_Goals"] = (
        season_data["home_goals"] + season_data["away_goals"]
    )
    season_data["Winning_Margin"] = (
        season_data["home_goals"] - season_data["away_goals"]
    ).abs()
    season_data = season_data.sort_values(
        ["match_date", "home_team", "away_team"],
        ascending=[False, True, True],
    )
    highest = season_data.loc[
        season_data["Total_Goals"] == season_data["Total_Goals"].max()
    ].copy()
    decided = season_data.loc[season_data["Winning_Margin"] > 0]
    biggest = decided.loc[
        decided["Winning_Margin"] == decided["Winning_Margin"].max()
    ].copy()
    return {
        "highest_scoring": highest.reset_index(drop=True),
        "biggest_wins": biggest.reset_index(drop=True),
    }


def get_club_biggest_wins(matches, season, team):
    """Largest victory margin for a specific club, including ties."""
    season_data = matches.loc[
        (matches["season"] == season)
        & (
            (matches["home_team"] == team)
            | (matches["away_team"] == team)
        )
    ].copy()
    if season_data.empty:
        return season_data

    at_home = season_data["home_team"] == team
    season_data["Goals_For"] = season_data["home_goals"].where(
        at_home, season_data["away_goals"]
    )
    season_data["Goals_Against"] = season_data["away_goals"].where(
        at_home, season_data["home_goals"]
    )
    season_data["Winning_Margin"] = (
        season_data["Goals_For"] - season_data["Goals_Against"]
    )
    season_data["Opponent"] = season_data["away_team"].where(
        at_home, season_data["home_team"]
    )
    season_data["Location"] = at_home.map({True: "Home", False: "Away"})
    wins = season_data.loc[season_data["Winning_Margin"] > 0].copy()
    if wins.empty:
        return wins
    return wins.loc[
        wins["Winning_Margin"] == wins["Winning_Margin"].max()
    ].sort_values("match_date", ascending=False).reset_index(drop=True)
