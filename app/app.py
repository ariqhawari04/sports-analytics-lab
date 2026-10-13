
from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import streamlit as st
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.performance import (
    get_cross_season_comparison,
    get_rolling_form,
    get_season_insights,
)

RAW_DIR = ROOT / "data" / "raw"

SEASONS = ["2024-25", "2025-26", "2026-27"]


st.set_page_config(
    page_title="Sports Analytics Lab",
    page_icon="⚽",
    layout="wide",
)


@st.cache_data
def load_matches():
    frames = []

    for season in SEASONS:
        filename = f"fbref_schedule_{season.replace('-', '_')}.csv"
        path = RAW_DIR / filename

        df = pd.read_csv(path)

        # Add the season explicitly
        df["season_label"] = season

        frames.append(df)

    matches = pd.concat(frames, ignore_index=True)

    # Extract goals from scores such as "2–1" or "2-1"
    score_parts = matches["score"].astype("string").str.extract(
        r"^\s*(\d+)\s*[-–—]\s*(\d+)\s*$"
    )

    matches["home_goals"] = pd.to_numeric(
        score_parts[0], errors="coerce"
    )
    matches["away_goals"] = pd.to_numeric(
        score_parts[1], errors="coerce"
    )

    matches["match_date"] = pd.to_datetime(
        matches["date"], errors="coerce"
    )

    matches["matchweek"] = pd.to_numeric(
        matches["week"], errors="coerce"
    )

    # Keep only completed matches
    matches = matches.dropna(
        subset=["home_goals", "away_goals", "match_date"]
    ).copy()

    return matches


def build_team_results(matches):
    home = pd.DataFrame({
        "season": matches["season_label"],
        "matchweek": matches["matchweek"],
        "match_date": matches["match_date"],
        "team": matches["home_team"],
        "opponent": matches["away_team"],
        "location": "Home",
        "goals_for": matches["home_goals"],
        "goals_against": matches["away_goals"],
    })

    away = pd.DataFrame({
        "season": matches["season_label"],
        "matchweek": matches["matchweek"],
        "match_date": matches["match_date"],
        "team": matches["away_team"],
        "opponent": matches["home_team"],
        "location": "Away",
        "goals_for": matches["away_goals"],
        "goals_against": matches["home_goals"],
    })

    results = pd.concat([home, away], ignore_index=True)

    results["result"] = "D"
    results.loc[
        results["goals_for"] > results["goals_against"],
        "result"
    ] = "W"
    results.loc[
        results["goals_for"] < results["goals_against"],
        "result"
    ] = "L"

    results["points"] = results["result"].map({
        "W": 3,
        "D": 1,
        "L": 0,
    })

    results = results.sort_values(
        ["season", "team", "match_date", "matchweek"]
    ).copy()

    results["cumulative_points"] = (
        results.groupby(["season", "team"])["points"].cumsum()
    )

    results["match_number"] = (
        results.groupby(["season", "team"]).cumcount() + 1
    )

    return results


def build_standings(results):
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

    table = table.sort_values(
        ["Pts", "GD", "GF"],
        ascending=[False, False, False]
    ).reset_index(drop=True)

    table.insert(0, "Position", table.index + 1)

    return table


# ==========================================
# APP
# ==========================================

st.title("⚽ Sports Analytics Lab")
st.caption("Premier League Performance Explorer · v0.1")

st.markdown(
    "Explore team performance, league standings, "
    "and points progression across Premier League seasons."
)

matches = load_matches()
all_results = build_team_results(matches)

season = st.selectbox(
    "Select season",
    SEASONS,
    index=2,
    format_func=lambda s: s.replace("-", "/"),
)

season_results = all_results[
    all_results["season"] == season
].copy()

season_matches = matches[
    matches["season_label"] == season
]

standings = build_standings(season_results)

st.subheader("League Overview")

col1, col2, col3 = st.columns(3)

col1.metric("Matches played", len(season_matches))
col2.metric("Teams", standings["team"].nunique())
col3.metric(
    "Latest result",
    season_matches["match_date"].max().strftime("%d %b %Y")
)

st.dataframe(
    standings,
    hide_index=True,
    use_container_width=True,
)

st.divider()

# ==========================================
# TEAM EXPLORER
# ==========================================

st.subheader("Team Performance Explorer")

teams = sorted(season_results["team"].unique())

default_team = (
    teams.index("Manchester Utd")
    if "Manchester Utd" in teams
    else 0
)

selected_team = st.selectbox(
    "Select team",
    teams,
    index=default_team,
)

team_results = season_results[
    season_results["team"] == selected_team
].copy()

team_stats = standings[
    standings["team"] == selected_team
].iloc[0]

c1, c2, c3, c4 = st.columns(4)

c1.metric("Position", f"#{int(team_stats['Position'])}")
c2.metric("Points", int(team_stats["Pts"]))
c3.metric("Wins", int(team_stats["W"]))
c4.metric("Goal difference", int(team_stats["GD"]))

# Points trajectory
fig = px.line(
    team_results,
    x="match_number",
    y="cumulative_points",
    markers=True,
    hover_data=[
        "opponent",
        "location",
        "result",
        "points",
    ],
    labels={
        "match_number": "Matches played",
        "cumulative_points": "Cumulative points",
    },
    title=f"{selected_team} — Points Progression",
)

fig.update_layout(
    xaxis=dict(dtick=1),
    yaxis=dict(rangemode="tozero"),
    hovermode="x unified",
)

st.plotly_chart(fig, use_container_width=True)


# ==========================================
# CROSS-SEASON PERFORMANCE
# ==========================================

st.divider()
st.subheader("Cross-Season Performance")

st.markdown(
    "How does this team's current points trajectory "
    "compare with previous seasons at the same "
    "number of matches?"
)

available_seasons = [
    s for s in SEASONS
    if not all_results[
        (all_results["team"] == selected_team)
        & (all_results["season"] == s)
    ].empty
]

if len(available_seasons) > 1:

    comparison, reference_matches = (
        get_cross_season_comparison(
            all_results,
            team=selected_team,
            reference_season=season,
        )
    )

    cross_season_fig = px.line(
        comparison,
        x="match_number",
        y="cumulative_points",
        color="season",
        markers=True,
        hover_data=[
            "opponent",
            "result",
            "points",
        ],
        labels={
            "match_number": "Matches played",
            "cumulative_points": "Cumulative points",
            "season": "Season",
        },
        title=(
            f"{selected_team} — "
            f"Season Trajectory Comparison"
        ),
    )

    cross_season_fig.update_layout(
        xaxis=dict(dtick=1),
        yaxis=dict(rangemode="tozero"),
        hovermode="x unified",
    )

    st.plotly_chart(
        cross_season_fig,
        use_container_width=True,
    )

    st.caption(
        f"Comparison limited to the first "
        f"{reference_matches} completed matches "
        f"of each available season."
    )

    
    # ==========================================
    # CROSS-SEASON SUMMARY
    # ==========================================

    season_snapshots = (
        comparison[
            comparison["match_number"] == reference_matches
        ][["season", "cumulative_points"]]
        .sort_values("season")
    )

    summary_parts = []

    for _, row in season_snapshots.iterrows():
        season_name = row["season"].replace("-", "/")
        points = int(row["cumulative_points"])

        summary_parts.append(
            f"{season_name}: {points} points"
        )

    summary_text = " | ".join(summary_parts)

    st.info(
        f"After {reference_matches} matches — "
        f"{selected_team}: {summary_text}"
    )


else:
    st.info(
        "Cross-season comparison is unavailable: "
        "this club appears in only one season."
    )



# ==========================================
# RECENT FORM & TRENDS
# ==========================================

st.divider()
st.subheader("Recent Form & Trends")

st.markdown(
    "See how the team performed in its most recent "
    "Premier League matches."
)

form_window = st.segmented_control(
    "Show recent matches",
    options=[5, 10],
    default=5,
    format_func=lambda n: f"Last {n} matches",
)

# Only take the most recent N matches
recent_matches = (
    team_results
    .sort_values(["match_date", "match_number"])
    .tail(form_window)
    .copy()
)

recent_points = int(recent_matches["points"].sum())
recent_count = len(recent_matches)
maximum_points = recent_count * 3

recent_ppg = (
    recent_points / recent_count
    if recent_count > 0 else 0
)

wins = int((recent_matches["result"] == "W").sum())
draws = int((recent_matches["result"] == "D").sum())
losses = int((recent_matches["result"] == "L").sum())

c1, c2, c3 = st.columns(3)

c1.metric(
    "Points earned",
    f"{recent_points} / {maximum_points}",
)

c2.metric(
    "Average points per match",
    f"{recent_ppg:.2f} / 3.00",
)

c3.metric(
    "Record (W-D-L)",
    f"{wins}-{draws}-{losses}",
)


# ==========================================
# RECENT MATCH RESULT BADGES
# ==========================================

form_colors = {
    "W": "#22c55e",
    "D": "#64748b",
    "L": "#ef4444",
}

st.markdown("**Match results (oldest → newest)**")

# Create one column for each match
result_columns = st.columns(
    len(recent_matches),
    gap="small"
)

for col, (_, match) in zip(
    result_columns,
    recent_matches.iterrows()
):
    result = match["result"]
    color = form_colors[result]

    with col:
        st.markdown(
            f'<div style="background-color:{color};'
            f'color:white;text-align:center;'
            f'border-radius:8px;padding:14px 0;'
            f'font-weight:700;font-size:20px;">'
            f'{result}</div>',
            unsafe_allow_html=True,
        )


st.caption(
    "Results shown from oldest to newest "
    "(left to right). "
    "W = Win, D = Draw, L = Loss."
)

# Detailed match results
with st.expander("View recent match details"):
    st.dataframe(
        recent_matches[
            [
                "match_date",
                "opponent",
                "location",
                "goals_for",
                "goals_against",
                "result",
                "points",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )

st.info(
    f"{selected_team} earned {recent_points} out of "
    f"{maximum_points} possible points in its last "
    f"{recent_count} Premier League matches, "
    f"with {wins} wins, {draws} draws, "
    f"and {losses} losses."
)


# Home vs Away
st.subheader("Home vs Away")

location_stats = (
    team_results.groupby("location", as_index=False)
    .agg(
        Matches=("points", "size"),
        Points=("points", "sum"),
        Goals_For=("goals_for", "sum"),
        Goals_Against=("goals_against", "sum"),
    )
)

st.dataframe(
    location_stats,
    hide_index=True,
    use_container_width=True,
)

# ==========================================
# TEAM COMPARISON
# ==========================================

st.divider()
st.subheader("Compare Teams")

default_comparison = [
    team for team in
    ["Manchester Utd", "Liverpool", "Arsenal"]
    if team in teams
]

comparison_teams = st.multiselect(
    "Choose teams",
    teams,
    default=default_comparison,
)

comparison = season_results[
    season_results["team"].isin(comparison_teams)
]

if not comparison.empty:
    comparison_fig = px.line(
        comparison,
        x="match_number",
        y="cumulative_points",
        color="team",
        markers=True,
        hover_data=["opponent", "result", "points"],
        labels={
            "match_number": "Matches played",
            "cumulative_points": "Cumulative points",
            "team": "Club",
        },
        title="Cumulative Points Comparison",
    )

    comparison_fig.update_layout(
        hovermode="x unified",
        yaxis=dict(rangemode="tozero"),
    )

    st.plotly_chart(comparison_fig, use_container_width=True)

st.divider()

st.caption(
    "Data source: FBref (via soccerdata). "
    "2026/27 is an ongoing season. "
    "Standings are calculated from completed matches; "
    "official tie-breakers beyond points, goal difference, "
    "and goals scored are not implemented."
)
