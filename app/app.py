import os
from dotenv import load_dotenv

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from src.processing.read_app_matches import (
    fetch_app_matches
)

from src.analysis.performance import get_cross_season_comparison

RAW_DIR = ROOT / "data" / "raw"
SEASONS = ["2024-25", "2025-26", "2026-27"]

BLUE = "#2563EB"
GREEN = "#16A34A"
RED = "#DC2626"
SLATE = "#64748B"
PALETTE = [BLUE, GREEN, "#F59E0B", "#8B5CF6", RED]

st.set_page_config(
    page_title="Sports Analytics Lab",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
<style>
.block-container {
    max-width: 1750px !important;
    padding: 2rem 2.5rem 3.5rem !important;
}

div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
}

.sal-hero {
    padding: 1.3rem 0 1.8rem;
}

.sal-eyebrow {
    color: #2563EB;
    font-size: 0.85rem;
    font-weight: 800;
    letter-spacing: 0.15em;
    margin-bottom: 0.65rem;
}

.sal-hero h1 {
    color: #0F172A;
    font-size: clamp(2.5rem, 4.5vw, 4.2rem);
    font-weight: 800;
    letter-spacing: -0.055em;
    line-height: 1.12;
    margin: 0;
}

.sal-hero h1 span {
    color: #2563EB;
}

.sal-subtitle {
    color: #64748B;
    font-size: 1.15rem;
    margin-top: 0.85rem;
}

@media (max-width: 768px) {
    .block-container {
        padding: 1.4rem 1rem 2rem !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# COMPACT HEADER & FULL-WIDTH NAVIGATION
# ==========================================

st.html("""
<style>

/* ========================================
   HEADER
   ======================================== */

.sal-topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    column-gap: 2rem;
    row-gap: 0.5rem;

    padding: 0.5rem 0 1.25rem;
    margin-bottom: 1rem;

    border-bottom: 1px solid #E2E8F0;
}

.sal-topbar .sal-brand {
    font-size: clamp(1.8rem, 2.8vw, 2.65rem) !important;
    font-weight: 800 !important;
    letter-spacing: -0.05em;
    line-height: 1.15 !important;

    color: #0F172A !important;
    margin: 0 !important;
    padding: 0 !important;
}

.sal-topbar .sal-brand span {
    color: #2563EB;
}

.sal-topbar .sal-tagline {
    font-size: 0.95rem;
    font-weight: 450;
    line-height: 1.4;
    color: #64748B;

    margin: 0;
    text-align: right;
}


/* ========================================
   FULL-WIDTH NAVIGATION
   ======================================== */

.stTabs [data-baseweb="tab-list"] {
    display: flex;
    width: 100%;
    gap: 10px;
    border-bottom: none;
}

.stTabs [data-baseweb="tab"] {
    flex: 1 1 0;
    min-width: 0;
    height: 52px;

    display: flex;
    justify-content: center;
    align-items: center;

    padding: 0 12px;
    border: 1px solid #E2E8F0;
    border-radius: 10px;

    background-color: #FFFFFF;
    color: #475569;
    font-weight: 600;

    transition: background-color 0.15s ease;
}

/* Selected tab */

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: #EFF6FF;
    border-color: #93C5FD;
    color: #1D4ED8;
}

/* Hover */

.stTabs [data-baseweb="tab"]:hover {
    background-color: #F1F5F9;
}

/* Hide default tab underline */

.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
    display: none;
}

/* Center the text */

.stTabs [data-baseweb="tab"] p {
    width: 100%;
    text-align: center;
    font-weight: 600;
}


/* ========================================
   MOBILE RESPONSIVENESS
   ======================================== */

@media (max-width: 650px) {

    .sal-topbar {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.35rem;
        padding-bottom: 1rem;
    }

    .sal-topbar .sal-brand {
        font-size: 1.75rem !important;
    }

    .sal-topbar .sal-tagline {
        font-size: 0.85rem;
        text-align: left;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
    }

    .stTabs [data-baseweb="tab"] {
        min-height: 50px;
        height: auto;
        padding: 8px 4px;
    }

    .stTabs [data-baseweb="tab"] p {
        font-size: 0.75rem;
        line-height: 1.2;
        white-space: normal;
    }

}

</style>
""")


# ==========================================
# MAIN NAVIGATION - FIXED STYLING
# ==========================================

st.html("""
<style>

/* Equal-width navigation */
.st-key-main_nav [role="tablist"] {
    display: grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    width: 100% !important;
    gap: 12px !important;
    border-bottom: none !important;
}

/* Navigation buttons */
.st-key-main_nav [role="tab"] {
    display: flex !important;
    width: 100% !important;
    min-width: 0 !important;
    min-height: 54px !important;
    justify-content: center !important;
    align-items: center !important;

    padding: 12px !important;
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;

    color: #475569 !important;
    font-weight: 600 !important;
    text-align: center !important;
}

/* Active navigation */
.st-key-main_nav [role="tab"][aria-selected="true"] {
    background: #EFF6FF !important;
    border-color: #93C5FD !important;
    color: #2563EB !important;
}

/* Text inside tabs */
.st-key-main_nav [role="tab"] p {
    margin: 0 !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    text-align: center !important;
    white-space: normal !important;
}

/* Remove default underline */
.st-key-main_nav [data-baseweb="tab-highlight"],
.st-key-main_nav [data-baseweb="tab-border"] {
    display: none !important;
}

/* Hover */
.st-key-main_nav [role="tab"]:hover {
    background: #F1F5F9 !important;
}

/* Mobile */
@media (max-width: 650px) {
    .st-key-main_nav [role="tablist"] {
        gap: 6px !important;
    }

    .st-key-main_nav [role="tab"] {
        padding: 8px 4px !important;
        min-height: 52px !important;
    }

    .st-key-main_nav [role="tab"] p {
        font-size: 12px !important;
        line-height: 1.3 !important;
    }
}

/* Right-align footer methodology button */
.st-key-sal_methodology {
    margin-left: auto !important;
    align-self: flex-end !important;
    width: fit-content !important;
}

</style>
""")


# ==========================================
# SEAMLESS NAVIGATION
# ==========================================

st.html("""
<style>

/* Join all three tabs into one navigation bar */
.st-key-main_nav [role="tablist"] {
    gap: 0 !important;
    border: 1px solid #DCE4ED !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Remove individual button borders and corners */
.st-key-main_nav [role="tab"] {
    border: none !important;
    border-right: 1px solid #DCE4ED !important;
    border-radius: 0 !important;
    background: #FFFFFF !important;
}

/* No divider after the final tab */
.st-key-main_nav [role="tab"]:last-of-type {
    border-right: none !important;
}

/* Selected tab */
.st-key-main_nav [role="tab"][aria-selected="true"] {
    background: #EFF6FF !important;
    color: #2563EB !important;
    box-shadow: inset 0 -3px 0 #2563EB !important;
}

/* Keep tabs joined on mobile too */
@media (max-width: 650px) {
    .st-key-main_nav [role="tablist"] {
        gap: 0 !important;
    }
}

</style>
""")



# ==========================================
# DATA
# ==========================================



@st.cache_data(ttl=900)
def load_matches():

    url = os.getenv("SUPABASE_URL")
    secret_key = os.getenv("SUPABASE_SECRET_KEY")

    # On Streamlit Cloud, credentials will be
    # provided through Secrets Management.
    if not url:
        url = st.secrets["SUPABASE_URL"]

    if not secret_key:
        secret_key = st.secrets["SUPABASE_SECRET_KEY"]

    return fetch_app_matches(url, secret_key)



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
        "W": 3, "D": 1, "L": 0
    })

    results = results.sort_values([
        "season", "team", "match_date", "matchweek"
    ]).copy()

    groups = results.groupby(["season", "team"])

    results["cumulative_points"] = (
        groups["points"].cumsum()
    )
    results["match_number"] = groups.cumcount() + 1

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


def style_chart(fig, height=420):
    """Consistent light style for all Plotly charts."""

    fig.update_layout(
        template="plotly_white",
        height=height,
        font=dict(
            size=15,
            color="#0F172A",
            family="Arial",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=15, t=55, b=30),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.22,
            x=0,
        ),
        hovermode="x unified",
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor="#CBD5E1",
    )
    fig.update_yaxes(
        gridcolor="rgba(148,163,184,0.20)",
        griddash="dot",
        zeroline=False,
        rangemode="tozero",
    )

    return fig


def show_recent_form(team_results):
    st.subheader("Recent Form")
    st.caption("Your team's latest Premier League results")

    window = st.segmented_control(
        "Show",
        options=[5, 10],
        default=5,
        format_func=lambda n: f"Last {n}",
    ) or 5

    recent = team_results.sort_values(
        "match_number"
    ).tail(window).copy()

    played = len(recent)
    points = int(recent["points"].sum())

    wins = int((recent["result"] == "W").sum())
    draws = int((recent["result"] == "D").sum())
    losses = int((recent["result"] == "L").sum())

    col1, col2 = st.columns(2)

    col1.metric("Points", f"{points} / {played * 3}")
    col2.metric(
        "Record (W-D-L)",
        f"{wins}-{draws}-{losses}"
    )

    st.caption("Oldest → Newest")

    colors = {
        "W": GREEN,
        "D": SLATE,
        "L": RED,
    }

    columns = st.columns(played, gap="small")

    for col, result in zip(columns, recent["result"]):
        color = colors[result]

        with col:
            st.markdown(
                f'<div style="background:{color};'
                f'color:white;text-align:center;'
                f'border-radius:7px;padding:10px 0;'
                f'font-size:15px;font-weight:700">'
                f'{result}</div>',
                unsafe_allow_html=True,
            )

    st.caption(
        f"{points} points from {played} matches "
        f"({points / played:.2f} per match)."
    )

    with st.expander("View match details"):
        details = recent[[
            "match_date", "opponent", "location",
            "goals_for", "goals_against", "result",
        ]].copy()

        details["match_date"] = (
            details["match_date"].dt.strftime("%d %b %Y")
        )

        st.dataframe(
            details,
            hide_index=True,
            use_container_width=True,
        )



# ==========================================
# LOAD APP DATA
# ==========================================

matches = load_matches()
all_results = build_team_results(matches)


# ==========================================
# BRAND HEADER
# ==========================================

st.html("""
<div class="sal-topbar">
    <h1 class="sal-brand">
        Sports Analytics Lab<span>.</span>
    </h1>
    <p class="sal-tagline">
        Beyond results. Understand performance.
    </p>
</div>
""")


# ==========================================
# MAIN NAVIGATION
# ==========================================

league_tab, team_tab, compare_tab = st.tabs(
    [
        "League Overview",
        "Team Explorer",
        "Comparison Lab",
    ],
    key="main_nav",
)

# ==========================================
# TAB 1 — LEAGUE OVERVIEW
# ==========================================

with league_tab:
    st.header("Premier League Overview")
    st.write(
        "Explore league standings and season performance."
    )

    filter_col, _ = st.columns([1, 3])

    with filter_col:
        league_season = st.selectbox(
            "Season",
            SEASONS,
            index=2,
            format_func=lambda s: s.replace("-", "/"),
            key="league_season",
        )

    league_matches = matches[
        matches["season_label"] == league_season
    ]

    league_results = all_results[
        all_results["season"] == league_season
    ]

    league_standings = build_standings(
        league_results
    )

    latest_date = (
        league_matches["match_date"]
        .max()
        .strftime("%d %b %Y")
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Completed matches",
        len(league_matches),
    )
    c2.metric(
        "Participating clubs",
        league_standings["team"].nunique(),
    )
    c3.metric("Latest result", latest_date)

    st.subheader("League Table")

    # Prepare league table for display
    display_standings = league_standings[[
        "Position", "team", "MP", "W",
        "D", "L", "GF", "GA", "GD", "Pts",
    ]].rename(columns={"team": "Team"})

    # Display league table
    st.dataframe(
        display_standings,
        hide_index=True,
        use_container_width=True,
        height=730,
    )


    st.caption(
        "Standings calculated from completed matches. "
        "Additional official tie-breakers are not applied."
    )


# ==========================================
# TAB 2 — TEAM EXPLORER
# ==========================================

with team_tab:
    st.header("Team Explorer")
    st.write(
        "Explore a club's performance, points progression, "
        "and recent results."
    )

    filter1, filter2 = st.columns(2)

    with filter1:
        team_season = st.selectbox(
            "Season",
            SEASONS,
            index=2,
            format_func=lambda s: s.replace("-", "/"),
            key="team_season",
        )

    team_season_results = all_results[
        all_results["season"] == team_season
    ]

    team_options = sorted(
        team_season_results["team"].unique()
    )

    default_team = (
        team_options.index("Manchester United FC")
        if "Manchester United FC" in team_options
        else 0
    )

    with filter2:
        selected_team = st.selectbox(
            "Club",
            team_options,
            index=default_team,
            key="team_club",
        )

    team_results = team_season_results[
        team_season_results["team"] == selected_team
    ].copy()

    standings = build_standings(
        team_season_results
    )

    team_stats = standings[
        standings["team"] == selected_team
    ].iloc[0]

    st.subheader(selected_team)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "League position",
        f"#{int(team_stats['Position'])}",
    )
    c2.metric("Points", int(team_stats["Pts"]))
    c3.metric("Wins", int(team_stats["W"]))
    c4.metric(
        "Goal difference",
        int(team_stats["GD"]),
    )

    st.write("")

    left, right = st.columns(
        [1.5, 1],
        gap="large",
    )

    with left:
        st.subheader("Points Progression")
        st.caption(
            "Total league points earned after each match"
        )

        fig = px.line(
            team_results,
            x="match_number",
            y="cumulative_points",
            markers=True,
            color_discrete_sequence=[BLUE],
            hover_data=[
                "opponent", "result", "points"
            ],
            labels={
                "match_number": "Matches played",
                "cumulative_points": "Total points",
            },
        )

        fig.update_traces(
            line=dict(
                color=BLUE,
                width=3.5,
                shape="linear",
            ),
            marker=dict(
                size=7,
                color=BLUE,
                line=dict(color="#F8FAFC", width=2),
            ),
            fill="tozeroy",
            fillcolor="rgba(37,99,235,0.09)",
        )

        fig.update_xaxes(
            dtick=1 if len(team_results) <= 10 else 5
        )

        st.plotly_chart(
            style_chart(fig),
            use_container_width=True,
            theme=None,
        )

    with right:
        show_recent_form(team_results)

    st.divider()

    with st.expander("Home vs Away Performance"):
        location_stats = (
            team_results
            .groupby("location", as_index=False)
            .agg(
                Matches=("points", "size"),
                Points=("points", "sum"),
                Goals_For=("goals_for", "sum"),
                Goals_Against=("goals_against", "sum"),
            )
        )

        location_stats["PPG"] = (
            location_stats["Points"]
            / location_stats["Matches"]
        ).round(2)

        st.dataframe(
            location_stats,
            hide_index=True,
            use_container_width=True,
        )


# ==========================================
# TAB 3 — COMPARISON LAB
# ==========================================

with compare_tab:
    st.header("Comparison Lab")
    st.write(
        "Compare club performance across seasons "
        "or against other Premier League teams."
    )

    mode = st.segmented_control(
        "Comparison type",
        ["Across seasons", "Between clubs"],
        default="Across seasons",
        key="comparison_mode",
    )

    
    if mode == "Across seasons":

        all_teams = sorted(all_results["team"].unique())

        default_club = (
            all_teams.index("Manchester United FC")
            if "Manchester United FC" in all_teams
            else 0
        )

        comparison_team = st.selectbox(
            "Choose club",
            all_teams,
            index=default_club,
            key="comparison_team",
        )

        available = [
            s for s in SEASONS
            if not all_results[
                (all_results["team"] == comparison_team)
                & (all_results["season"] == s)
            ].empty
        ]

        selected_seasons = st.multiselect(
            "Choose seasons",
            available,
            default=available,
            format_func=lambda s: s.replace("-", "/"),
            key="cross_seasons",
        )

        if not selected_seasons:
            st.info("Select at least one season.")

        else:
            # Filter to selected team and seasons
            comparison = all_results[
                (all_results["team"] == comparison_team)
                & (
                    all_results["season"].isin(
                        selected_seasons
                    )
                )
            ].copy()

            # Number of matches available in each season
            counts = (
                comparison.groupby("season")["match_number"]
                .max()
                .to_dict()
            )

            view_mode = st.segmented_control(
                "Timeline",
                options=[
                    "Full available seasons",
                    "First N matches",
                ],
                default="Full available seasons",
                key="cross_view_mode",
            )

            if view_mode == "First N matches":
                # Equal-length comparison
                max_common = int(min(counts.values()))

                if max_common > 1:
                    n_matches = st.slider(
                        "Compare first N matches",
                        min_value=1,
                        max_value=max_common,
                        value=max_common,
                        key="cross_match_limit",
                    )
                else:
                    n_matches = 1
                    st.caption(
                        "Only one completed match "
                        "is available for comparison."
                    )

                comparison = comparison[
                    comparison["match_number"] <= n_matches
                ].copy()

                st.caption(
                    f"Comparing the first {n_matches} "
                    "completed matches of each season."
                )

            else:
                st.caption(
                    "Showing all completed matches "
                    "available for each season. "
                    "Ongoing seasons end at their "
                    "latest completed match."
                )

            # Consistent season colours
            season_colors = {
                "2024-25": "#2563EB",
                "2025-26": "#16A34A",
                "2026-27": "#F59E0B",
            }

            # Visualisation
            fig = px.line(
                comparison,
                x="match_number",
                y="cumulative_points",
                color="season",
                markers=True,
                color_discrete_map=season_colors,
                hover_data=[
                    "opponent",
                    "result",
                    "points",
                ],
                labels={
                    "match_number": "Matches played",
                    "cumulative_points": "Total points",
                    "season": "Season",
                },
            )

            fig.update_traces(
                line=dict(width=3),
                marker=dict(size=6),
            )

            max_displayed = int(
                comparison["match_number"].max()
            )

            fig.update_xaxes(
                dtick=1 if max_displayed <= 10 else 5
            )

            st.plotly_chart(
                style_chart(fig, height=460),
                use_container_width=True,
                theme=None,
            )

            # One summary card per selected season
            snapshots = (
                comparison
                .sort_values(["season", "match_number"])
                .groupby("season")
                .tail(1)
                .sort_values("season")
            )

            cols = st.columns(len(snapshots))

            for col, (_, row) in zip(
                cols,
                snapshots.iterrows(),
            ):
                with col:
                    st.metric(
                        row["season"].replace("-", "/"),
                        f"{int(row['cumulative_points'])} pts",
                    )
                    st.caption(
                        f"After {int(row['match_number'])} "
                        "matches"
                    )


    else:
        comparison_season = st.selectbox(
            "Season",
            SEASONS,
            index=2,
            format_func=lambda s: s.replace("-", "/"),
            key="comparison_season",
        )

        season_data = all_results[
            all_results["season"] == comparison_season
        ]

        available_clubs = sorted(
            season_data["team"].unique()
        )

        defaults = [
            club for club in [
                "Manchester United FC",
                "Liverpool",
                "Arsenal",
            ]
            if club in available_clubs
        ]

        chosen_clubs = st.multiselect(
            "Choose clubs",
            available_clubs,
            default=defaults,
            key="comparison_clubs",
        )

        comparison = season_data[
            season_data["team"].isin(chosen_clubs)
        ]

        if comparison.empty:
            st.info("Select at least one club.")

        else:
            fig = px.line(
                comparison,
                x="match_number",
                y="cumulative_points",
                color="team",
                markers=True,
                color_discrete_sequence=PALETTE,
                hover_data=[
                    "opponent", "result", "points"
                ],
                labels={
                    "match_number": "Matches played",
                    "cumulative_points": "Total points",
                    "team": "Club",
                },
            )

            fig.update_traces(
                line=dict(width=3)
            )

            st.plotly_chart(
                style_chart(fig, height=460),
                use_container_width=True,
            )

            st.caption(
                "Comparison uses matches played, "
                "not calendar dates."
            )



# ==========================================
# FOOTER & METHODOLOGY
# ==========================================

st.divider()

footer_left, footer_right = st.columns([4, 1])

with footer_left:
    st.caption(
        "Sports Analytics Lab · v0.1 · Premier League 2024–2027"
    )

    # Visible data source attribution
    st.caption(
        "Football data provided by the Football-Data.org API "
        "· Historical results: OpenFootball (CC0)"
    )

with footer_right:
    with st.popover(
        "Data & Methodology",
        type="tertiary",
        key="sal_methodology",
    ):
        st.markdown(
            """
            **Data sources**

            - **2024/25 and 2025/26:** OpenFootball (CC0 / public domain)
            - **2026/27:** football-data.org API

            **Data freshness**

            The current season uses the latest
            successfully retrieved API snapshot.
            Data is not updated in real time.

            **Points calculation**

            - Win = 3 points
            - Draw = 1 point
            - Loss = 0 points

            **Cross-season comparison**

            Teams are compared by matches played,
            not calendar dates.

            **Limitations**

            Standings are calculated independently
            by Sports Analytics Lab.

            Strength of schedule is not adjusted.
            Additional official league tie-breakers
            are not implemented.
            """
        )

