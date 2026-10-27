
"""
SAL v0.3 — Local Multi-League Preview

Explore validated historical match datasets.
No Supabase connection required.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.match_results import build_team_results
from src.analysis.standings import build_standings


DATA_PATH = (
    ROOT / "data" / "processed"
    / "multi_league_historical_preview.csv"
)

LEAGUE_NAMES = {
    "BL1": "Bundesliga",
    "FL1": "Ligue 1",
    "PD": "La Liga",
    "SA": "Serie A",
}


st.set_page_config(
    page_title="SAL — Multi-League Preview",
    page_icon="⚽",
    layout="wide",
)



# ========================================
# NAVBAR — CLEAN LEAGUE MENU
# ========================================

league_code = st.query_params.get(
    "league", "BL1"
)

if league_code not in LEAGUE_NAMES:
    league_code = "BL1"

# Position navigation closer to the brand.
brand_col, nav_col, spacer_col = st.columns(
    [3, 2, 7],
    gap="small",
    vertical_alignment="center",
)

with brand_col:
    st.title("Sports Analytics Lab.")

with nav_col:
    selected_league = st.menu_button(
        f"Football / {LEAGUE_NAMES[league_code]}",
        options=[
            code for code in LEAGUE_NAMES
            if code != league_code
        ],
        format_func=lambda code: LEAGUE_NAMES[code],
        type="tertiary",
        width="content",
        key="sal_league_menu",
    )

# Update browser URL when a league is selected.
if selected_league is not None:
    st.query_params.from_dict({
        "sport": "football",
        "league": selected_league,
    })
    st.rerun()

st.subheader(
    "Multi-League Analytics — v0.3 Preview"
)

st.caption(
    "Local development preview | "
    "Historical completed matches | "
    "Source: OpenFootball"
)



# ========================================
# LOAD DATA
# ========================================

if not DATA_PATH.exists():
    st.error(
        "Dataset not found. Run "
        "python -m src.processing."
        "build_multi_league_preview first."
    )
    st.stop()

matches = pd.read_csv(
    DATA_PATH,
    parse_dates=["match_date"],
)


# ========================================
# SEASON FILTER
# League selection is handled by navbar.
# ========================================

available_seasons = sorted(
    matches.loc[
        matches["league_code"] == league_code,
        "season",
    ].unique(),
    reverse=True,
)

season = st.selectbox(
    "Select Season",
    options=available_seasons,
    format_func=lambda s: s.replace("-", "/"),
    key=f"preview_season_{league_code}",
)

selected = matches.loc[
    (matches["league_code"] == league_code)
    & (matches["season"] == season)
].copy()

results = build_team_results(selected)
standings = build_standings(results)

st.divider()

# ========================================
# LEAGUE SUMMARY
# ========================================

total_goals = (
    selected["home_goals"]
    + selected["away_goals"]
).sum()

home_wins = (
    selected["home_goals"]
    > selected["away_goals"]
).sum()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Completed Matches", len(selected))
c2.metric("Participating Clubs", len(standings))

c3.metric(
    "Goals per Match",
    f"{total_goals / len(selected):.2f}",
)

c4.metric(
    "Home Win Rate",
    f"{home_wins / len(selected):.1%}",
)

# ========================================
# LEAGUE STANDINGS
# ========================================

st.subheader("League Standings")

display_columns = [
    "Position",
    "team",
    "MP",
    "W",
    "D",
    "L",
    "GF",
    "GA",
    "GD",
    "Pts",
]

st.dataframe(
    standings[display_columns],
    hide_index=True,
    width="stretch",
)

# ========================================
# POINTS COMPARISON
# ========================================

st.subheader("Top 10 Clubs — Points")

top_10 = standings.head(10).copy()

fig = px.bar(
    top_10.sort_values("Pts"),
    x="Pts",
    y="team",
    orientation="h",
    labels={"team": "Club", "Pts": "Points"},
    text="Pts",
)

fig.update_layout(
    template="plotly_white",
    height=480,
    showlegend=False,
    margin=dict(l=10, r=20, t=20, b=20),
)

st.plotly_chart(
    fig,
    width="stretch",
)

st.caption(
    "Standings are calculated from match results. "
    "Official tie-breakers and deductions may "
    "require additional league-specific rules."
)
