
import pandas as pd


def get_cross_season_comparison(
    results,
    team,
    reference_season="2026-27"
):
    """
    Compare a team's points progression across seasons,
    using the same number of matches as the reference season.
    """

    team_data = results[
        results["team"] == team
    ].copy()

    reference = team_data[
        team_data["season"] == reference_season
    ]

    if reference.empty:
        raise ValueError(
            f"No data for {team} in {reference_season}"
        )

    reference_matches = int(reference["match_number"].max())

    comparison = team_data[
        team_data["match_number"] <= reference_matches
    ].copy()

    return comparison, reference_matches


def get_rolling_form(results, window=5):
    """
    Calculate rolling points per match for each
    team and season.

    A full window is required for comparable results.
    """

    data = results.sort_values(
        ["season", "team", "match_number"]
    ).copy()

    data["rolling_ppg"] = (
        data.groupby(["season", "team"])["points"]
        .transform(
            lambda x: x.rolling(
                window=window,
                min_periods=window
            ).mean()
        )
    )

    return data


def get_season_insights(
    comparison,
    team,
    reference_season,
    reference_matches
):
    """
    Generate factual, descriptive comparisons
    from equal-length season samples.
    """

    snapshots = (
        comparison[
            comparison["match_number"] == reference_matches
        ][["season", "cumulative_points"]]
        .set_index("season")["cumulative_points"]
        .to_dict()
    )

    current_points = snapshots.get(reference_season)

    if current_points is None:
        return []

    insights = []

    for season, previous_points in sorted(snapshots.items()):
        if season == reference_season:
            continue

        difference = current_points - previous_points

        if difference > 0:
            description = f"{difference:+.0f} points ahead"
        elif difference < 0:
            description = f"{difference:+.0f} points behind"
        else:
            description = "level on points"

        insights.append(
            f"{team} are {description} of their "
            f"{season.replace('-', '/')} total after "
            f"{reference_matches} matches "
            f"({current_points:.0f} vs "
            f"{previous_points:.0f})."
        )

    return insights
