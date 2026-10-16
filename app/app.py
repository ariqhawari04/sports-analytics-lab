import os
from dotenv import load_dotenv

from pathlib import Path
import sys

import pandas as pd

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import streamlit as st

from html import escape


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from src.processing.read_app_matches import (
    fetch_app_matches
)

from src.analysis.performance import get_cross_season_comparison
from src.analysis.head_to_head import get_head_to_head

from src.analysis.league_records import (
    build_club_records,
    get_match_extremes,
    get_club_biggest_wins,
)

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
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
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

    def get_credential(name):
        return (
            os.getenv(name)
            or st.secrets[name]
        )

    return fetch_app_matches(
        host=get_credential("SUPABASE_POOLER_HOST"),
        user=get_credential("SUPABASE_READER_USER"),
        password=get_credential("SUPABASE_READER_PASSWORD"),
    )




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
        There's more to the game than just the score.
    </p>
</div>
""")


# ==========================================
# MAIN NAVIGATION
# ==========================================

league_tab, team_tab, compare_tab, h2h_tab = st.tabs(
    [
        "League Overview",
        "Team Explorer",
        "Team Comparison",
        "Head-to-Head",
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

    # ======================================
    # LAST 5 MATCHES FORM
    # ======================================

    # league_results already contains only
    # matches from the selected season.
    recent_form = (
        league_results
        .sort_values(["team", "match_number"])
        .groupby("team")["result"]
        .apply(lambda results: list(results.tail(5)))
        .to_dict()
    )

    form_classes = {
        "W": "win",
        "D": "draw",
        "L": "loss",
    }

    form_labels = {
        "W": "Win",
        "D": "Draw",
        "L": "Loss",
    }

    # ======================================
    # BUILD LEAGUE TABLE ROWS
    # ======================================

    rows_html = []

    for row in league_standings.itertuples(index=False):

        team_form = recent_form.get(row.team, [])

        badges = "".join(
            (
                f'<span class="sal-form-badge '
                f'sal-form-{form_classes[result]}" '
                f'title="{form_labels[result]}">'
                f'{result}</span>'
            )
            for result in team_form
        )

        if not badges:
            badges = '<span class="sal-form-empty">—</span>'

        rows_html.append(
            f"""
            <tr>
                <td>{row.Position}</td>
                <td class="sal-league-team">
                    {escape(str(row.team))}
                </td>
                <td>{row.MP}</td>
                <td>{row.W}</td>
                <td>{row.D}</td>
                <td>{row.L}</td>
                <td>{row.GF}</td>
                <td>{row.GA}</td>
                <td>{row.GD}</td>
                <td class="sal-league-points">{row.Pts}</td>
                <td class="sal-league-form">
                    <div class="sal-form-list">
                        {badges}
                    </div>
                </td>
            </tr>
            """
        )

    table_rows = "\n".join(rows_html)

    # ======================================
    # LEAGUE TABLE STYLING
    # ======================================

    table_css = """
    <style>

    .sal-league-scroll {
        width: 100%;
        max-height: none;
        overflow-x: auto;
        overflow-y: hidden;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        background: #FFFFFF;
    }

    .sal-league-table {
        width: 100%;
        min-width: 1000px;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 14px;
        color: #0F172A;
    }

    .sal-league-table th {
        position: sticky;
        top: 0;
        z-index: 1;
        background: #F1F5F9;
        color: #64748B;
        font-weight: 500;
        text-align: right;
        white-space: nowrap;
        padding: 12px 10px;
        border-bottom: 1px solid #E2E8F0;
    }

    .sal-league-table td {
        text-align: right;
        padding: 10px;
        border-bottom: 1px solid #F1F5F9;
        white-space: nowrap;
    }

    .sal-league-table th:nth-child(2),
    .sal-league-table td:nth-child(2),
    .sal-league-table th:last-child,
    .sal-league-table td:last-child {
        text-align: left;
    }

    .sal-league-table tbody tr:hover {
        background: #F8FAFC;
    }

    .sal-league-table tbody tr:last-child td {
        border-bottom: none;
    }

    .sal-league-team {
        font-weight: 500;
        min-width: 180px;
    }

    .sal-league-points {
        font-weight: 700;
    }

    .sal-form-list {
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .sal-form-badge {
        display: inline-flex;
        justify-content: center;
        align-items: center;
        width: 23px;
        height: 23px;
        border-radius: 5px;
        color: #FFFFFF;
        font-size: 12px;
        font-weight: 700;
    }

    .sal-form-win {
        background: #16A34A;
    }

    .sal-form-draw {
        background: #94A3B8;
    }

    .sal-form-loss {
        background: #DC2626;
    }

    .sal-form-empty {
        color: #94A3B8;
    }

    .sal-league-form {
        min-width: 160px;
    }

    /* ========================================
    BALANCED LEAGUE TABLE COLUMNS
    ======================================== */

    /* Prevent uneven automatic column sizing */
    .sal-league-table {
        table-layout: fixed;
        width: 100%;
        min-width: 1080px;
    }

    /* Position */
    .sal-league-table th:nth-child(1) {
        width: 7%;
    }

    /* Team name */
    .sal-league-table th:nth-child(2) {
        width: 22%;
    }

    /* MP, W, D, L, GF, GA, GD */
    .sal-league-table th:nth-child(n+3):nth-child(-n+9) {
        width: 6.5%;
    }

    /* Points */
    .sal-league-table th:nth-child(10) {
        width: 8.5%;
    }

    /* Form (Last 5) */
    .sal-league-table th:nth-child(11) {
        width: 17%;
    }

    /* Compact padding and align numeric data */
    .sal-league-table th,
    .sal-league-table td {
        padding: 9px 6px;
        text-align: center;
    }

    /* Team names stay left-aligned */
    .sal-league-table th:nth-child(2),
    .sal-league-table td:nth-child(2) {
        text-align: left;
        padding-left: 12px;
    }

    /* Center Form column header and contents */
    .sal-league-table th:last-child,
    .sal-league-table td:last-child {
        text-align: center;
        padding-left: 6px;
        padding-right: 6px;
    }

    /* Center the W-D-L badges within the Form column */
    .sal-form-list {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        width: 100%;
    }

    /* ========================================
    MOBILE HORIZONTAL SCROLL HINT
    ======================================== */

    .sal-swipe-hint {
        display: none;
    }

    @media (max-width: 768px) {
        .sal-swipe-hint {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;

            margin-top: 8px;
            margin-bottom: 0;
            padding: 8px 12px;

            color: #64748B;
            font-size: 12px;
            font-weight: 500;
        }
    }

    </style>
    """

    # ======================================
    # RENDER LEAGUE TABLE
    # ======================================

    table_html = f"""
    <div class="sal-league-scroll">
        <table class="sal-league-table">
            <thead>
                <tr>
                    <th>Position</th>
                    <th>Team</th>
                    <th>MP</th>
                    <th>W</th>
                    <th>D</th>
                    <th>L</th>
                    <th>GF</th>
                    <th>GA</th>
                    <th>GD</th>
                    <th>Pts</th>
                    <th>Form (Last 5)</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>

    <div class="sal-swipe-hint">
        <span aria-hidden="true">↔</span>
        <span>Swipe horizontally to view all statistics</span>
    </div>
    """


    st.html(table_css + table_html)

    st.caption(
        "Form shows the last five completed matches "
        "in chronological order (oldest to newest). "
        "W = Win, D = Draw, L = Loss."
    )



    st.caption(
        "Standings calculated from completed matches. "
        "Additional official tie-breakers are not applied."
    )

    
    # ======================================
    # SEASON RECORDS & INSIGHTS
    # ======================================

    st.divider()

    st.subheader("Season Records & Insights")

    st.caption(
        "Standout performances and match records "
        "from the selected Premier League season."
    )

    club_records = build_club_records(
        all_results,
        league_season,
    )

    match_records = get_match_extremes(
        league_matches,
        league_season,
    )

    # Include joint record holders, rather than
    # displaying only the first club.
    def record_leader(metric):
        eligible = club_records.dropna(
            subset=[metric]
        )

        if eligible.empty:
            return None, "No matches available"

        record = eligible[metric].max()

        clubs = sorted(
            eligible.loc[
                eligible[metric] == record, "team"
            ].tolist()
        )

        if len(clubs) <= 2:
            club_label = " · ".join(clubs)
        else:
            club_label = (
                " · ".join(clubs[:2])
                + f" · +{len(clubs) - 2} tied"
            )

        return record, club_label

    # ==================================
    # CLUB PERFORMANCE RECORDS
    # ==================================

    winning_record, winning_clubs = record_leader(
        "Longest_Winning_Streak"
    )

    unbeaten_record, unbeaten_clubs = record_leader(
        "Longest_Unbeaten_Streak"
    )

    clean_sheet_record, clean_sheet_clubs = record_leader(
        "Clean_Sheets"
    )

    home_record, home_clubs = record_leader(
        "Home_PPG"
    )

    away_record, away_clubs = record_leader(
        "Away_PPG"
    )

    record_col1, record_col2, record_col3 = (
        st.columns(3)
    )

    with record_col1:
        st.metric(
            "Longest Winning Streak",
            f"{int(winning_record)} matches",
        )
        st.caption(winning_clubs)

    with record_col2:
        st.metric(
            "Longest Unbeaten Streak",
            f"{int(unbeaten_record)} matches",
        )
        st.caption(unbeaten_clubs)

    with record_col3:
        st.metric(
            "Most Clean Sheets",
            int(clean_sheet_record),
        )
        st.caption(clean_sheet_clubs)

    home_col, away_col = st.columns(2)

    with home_col:
        st.metric(
            "Best Home Points per Match",
            f"{home_record:.2f}"
            if home_record is not None else "—",
        )
        st.caption(home_clubs)

    with away_col:
        st.metric(
            "Best Away Points per Match",
            f"{away_record:.2f}"
            if away_record is not None else "—",
        )
        st.caption(away_clubs)

    # ==================================
    # STANDOUT MATCH RECORDS
    # ==================================

    st.markdown("**Standout Matches**")

    highest_scoring = match_records[
        "highest_scoring"
    ]

    biggest_wins = match_records[
        "biggest_wins"
    ]

    match_col1, match_col2 = st.columns(2)

    with match_col1:
        top_match = highest_scoring.iloc[0]

        st.metric(
            "Highest-Scoring Match",
            f"{int(top_match['Total_Goals'])} goals",
        )

        st.caption(
            f"{top_match['home_team']} "
            f"{int(top_match['home_goals'])}–"
            f"{int(top_match['away_goals'])} "
            f"{top_match['away_team']}"
        )

        if len(highest_scoring) > 1:
            st.caption(
                f"{len(highest_scoring)} matches "
                "share this record."
            )

    with match_col2:
        if biggest_wins.empty:
            st.metric(
                "Biggest Victory",
                "—",
            )
            st.caption("No decisive result yet.")

        else:
            top_win = biggest_wins.iloc[0]

            st.metric(
                "Biggest Victory",
                f"{int(top_win['Winning_Margin'])} "
                "goals",
            )

            st.caption(
                f"{top_win['home_team']} "
                f"{int(top_win['home_goals'])}–"
                f"{int(top_win['away_goals'])} "
                f"{top_win['away_team']}"
            )

            if len(biggest_wins) > 1:
                st.caption(
                    f"{len(biggest_wins)} matches "
                    "share this record."
                )

    # ==================================
    # DETAILED CLUB LEADERBOARD
    # ==================================

    

    # ======================================
    # INTERACTIVE SEASON RECORDS LEADERBOARD
    # ======================================

    with st.expander(
        "Explore Full Season Records",
        expanded=False,
    ):

        # Metric and appropriate match-count column
        record_metrics = {
            "Clean Sheets": ("Clean_Sheets", "MP"),
            "Winning Streak": (
                "Longest_Winning_Streak", "MP"
            ),
            "Unbeaten Streak": (
                "Longest_Unbeaten_Streak", "MP"
            ),
            "Home Points per Match": (
                "Home_PPG", "Home_MP"
            ),
            "Away Points per Match": (
                "Away_PPG", "Away_MP"
            ),
        }

        selected_record = st.selectbox(
            "Rank clubs by",
            options=list(record_metrics.keys()),
            key="league_records_metric",
        )

        metric_column, matches_column = (
            record_metrics[selected_record]
        )

        # ==================================
        # PREPARE COMPLETE LEAGUE DATA
        # ==================================

        leaderboard = club_records[
            ["team", metric_column, matches_column]
        ].dropna(
            subset=[metric_column]
        ).copy()

        leaderboard = leaderboard.sort_values(
            [metric_column, "team"],
            ascending=[False, True],
        )

        # Arithmetic mean across eligible clubs.
        league_average = float(
            leaderboard[metric_column].mean()
        )

        is_ppg = metric_column.endswith("PPG")

        average_label = (
            f"{league_average:.2f}"
            if is_ppg
            else f"{league_average:.1f}"
        )

        st.caption(
            f"League average: {average_label} "
            f"· {len(leaderboard)} clubs included"
        )

        # ==================================
        # COLOUR BY LEAGUE AVERAGE
        # ==================================

        # Plotly horizontal bars display
        # the final row at the top.
        chart_data = leaderboard.iloc[::-1].copy()

        bar_colors = [
            BLUE
            if value >= league_average
            else "#CBD5E1"
            for value in chart_data[metric_column]
        ]

        value_labels = [
            f"{value:.2f}" if is_ppg else f"{value:.0f}"
            for value in chart_data[metric_column]
        ]

        # ==================================
        # FULL LEAGUE BAR CHART
        # ==================================

        fig_records = go.Figure()

        fig_records.add_trace(
            go.Bar(
                x=chart_data[metric_column],
                y=chart_data["team"],
                orientation="h",

                marker=dict(
                    color=bar_colors,
                    line=dict(width=0),
                ),

                text=value_labels,
                textposition="outside",
                cliponaxis=False,

                customdata=chart_data[
                    [matches_column]
                ].to_numpy(),

                hovertemplate=(
                    "<b>%{y}</b>"
                    f"<br>{selected_record}: "
                    + ("%{x:.2f}" if is_ppg else "%{x:.0f}")
                    + "<br>Matches in sample: "
                    "%{customdata[0]}"
                    "<extra></extra>"
                ),

                showlegend=False,
            )
        )

        # ==================================
        # LEAGUE AVERAGE REFERENCE LINE
        # ==================================

        fig_records.add_vline(
            x=league_average,
            line_width=2,
            line_dash="dash",
            line_color="#64748B",
        )

        max_value = float(
            leaderboard[metric_column].max()
        )

        fig_records.update_layout(
            template="plotly_white",
            height=max(480, len(chart_data) * 32 + 75),

            margin=dict(
                l=10,
                r=65,
                t=20,
                b=45,
            ),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",

            font=dict(
                size=13,
                color="#0F172A",
            ),

            showlegend=False,
            xaxis_title=selected_record,
            yaxis_title=None,
            bargap=0.28,
        )

        fig_records.update_xaxes(
            range=[
                0,
                max(1.0, max_value * 1.18),
            ],
            gridcolor="rgba(148,163,184,0.15)",
            zeroline=False,
            fixedrange=True,
        )

        fig_records.update_yaxes(
            automargin=True,
            showgrid=False,
            fixedrange=True,
        )

        st.plotly_chart(
            fig_records,
            use_container_width=True,
            theme=None,
            key="league_records_leaderboard_chart",
        )

        # ==================================
        # CHART EXPLANATION
        # ==================================

        st.caption(
            "Blue = at or above league average "
            "· Grey = below league average "
            "· Dashed line = league average."
        )

        if is_ppg:
            st.caption(
                "Home and away PPG are calculated "
                "using completed matches at the "
                "selected venue. Clubs without "
                "eligible matches are excluded."
            )
        else:
            st.caption(
                "Records are calculated using each "
                "club's completed matches. "
                "Streaks follow chronological "
                "match order."
            )

    st.caption(
        "Records are based on completed Premier League "
        "matches in the selected season. Home and away "
        "PPG are calculated from matches played at each "
        "venue; early-season comparisons may involve "
        "different sample sizes."
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

    
    # ======================================
    # CLUB RECORDS & MILESTONES
    # ======================================

    st.subheader("Club Records & Milestones")

    st.caption(
        f"Notable records for {selected_team} "
        f"in the {team_season.replace('-', '/')} season."
    )

    season_club_records = build_club_records(
        team_season_results,
        team_season,
    )

    selected_club_record = (
        season_club_records.loc[
            season_club_records["team"] == selected_team
        ].iloc[0]
    )

    biggest_club_wins = get_club_biggest_wins(
        matches,
        team_season,
        selected_team,
    )

    # ==================================
    # WINNING & UNBEATEN STREAKS
    # ==================================

    streak_col1, streak_col2 = st.columns(2)

    with streak_col1:
        st.metric(
            "Longest Winning Streak",
            f"{int(selected_club_record['Longest_Winning_Streak'])} "
            "matches",
        )

    with streak_col2:
        st.metric(
            "Longest Unbeaten Streak",
            f"{int(selected_club_record['Longest_Unbeaten_Streak'])} "
            "matches",
        )

    # ==================================
    # CLEAN SHEETS & BIGGEST VICTORY
    # ==================================

    club_col1, club_col2 = st.columns(2)

    with club_col1:
        st.metric(
            "Clean Sheets",
            int(selected_club_record["Clean_Sheets"]),
        )

        st.caption(
            "Completed matches without conceding."
        )

    with club_col2:
        if biggest_club_wins.empty:
            st.metric(
                "Biggest Victory",
                "—",
            )

            st.caption(
                "No victories recorded in this season yet."
            )

        else:
            biggest_win = biggest_club_wins.iloc[0]

            victory_margin = int(
                biggest_win["Winning_Margin"]
            )

            goals_for = int(
                biggest_win["Goals_For"]
            )

            goals_against = int(
                biggest_win["Goals_Against"]
            )

            st.metric(
                "Biggest Victory",
                f"{victory_margin}-goal margin",
            )

            st.caption(
                f"vs {biggest_win['Opponent']} "
                f"({biggest_win['Location']}) "
                f"· {goals_for}–{goals_against}"
            )

            if len(biggest_club_wins) > 1:
                st.caption(
                    f"{len(biggest_club_wins)} victories "
                    "share this record."
                )

    st.caption(
        "Records reflect completed matches in the "
        "selected season, not all-time club records."
    )

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

    
    # ======================================
    # COMPARE ACROSS SEASONS
    # ======================================

    with st.expander("Compare Across Seasons", expanded=False):

        st.caption(
            f"Compare {selected_team}'s points progression "
            "across different Premier League seasons."
        )

        # Use the club selected in Team Explorer.
        # No need to select the same club again.
        team_history = all_results[
            all_results["team"] == selected_team
        ].copy()

        available_seasons = [
            season
            for season in SEASONS
            if season in team_history["season"].unique()
        ]

        compare_seasons = st.multiselect(
            "Choose seasons",
            options=available_seasons,
            default=available_seasons,
            format_func=lambda s: s.replace("-", "/"),
            key="team_compare_seasons",
        )

        if not compare_seasons:
            st.info("Select at least one season.")

        else:
            comparison_data = team_history[
                team_history["season"].isin(compare_seasons)
            ].copy()

            # Number of completed matches in each season
            season_counts = (
                comparison_data
                .groupby("season")["match_number"]
                .max()
                .to_dict()
            )

            compare_view = st.segmented_control(
                "Timeline",
                options=[
                    "Full available seasons",
                    "First N matches",
                ],
                default="Full available seasons",
                key="team_compare_view",
            )

            if compare_view == "First N matches":

                max_common = int(
                    min(season_counts.values())
                )

                if max_common > 1:
                    n_matches = st.slider(
                        "Compare first N matches",
                        min_value=1,
                        max_value=max_common,
                        value=max_common,
                        key="team_compare_match_limit",
                    )
                else:
                    n_matches = 1
                    st.caption(
                        "Only one completed match is "
                        "available for comparison."
                    )

                comparison_data = comparison_data[
                    comparison_data["match_number"] <= n_matches
                ].copy()

                st.caption(
                    f"Comparing the first {n_matches} "
                    "completed matches of each season."
                )

            else:
                st.caption(
                    "Showing all completed matches available "
                    "for each selected season. "
                    "Ongoing seasons end at their latest "
                    "completed match."
                )

            # Consistent season colours
            season_colors = {
                "2024-25": "#2563EB",
                "2025-26": "#16A34A",
                "2026-27": "#F59E0B",
            }

            # ==================================
            # POINTS PROGRESSION CHART
            # ==================================

            fig_cross = px.line(
                comparison_data,
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

            fig_cross.update_traces(
                line=dict(width=3),
                marker=dict(size=6),
            )

            max_displayed = int(
                comparison_data["match_number"].max()
            )

            fig_cross.update_xaxes(
                dtick=1 if max_displayed <= 10 else 5
            )

            st.plotly_chart(
                style_chart(fig_cross, height=460),
                use_container_width=True,
                theme=None,
                key="team_explorer_cross_seasons_chart",
            )

            # ==================================
            # SEASON SUMMARY CARDS
            # ==================================

            snapshots = (
                comparison_data
                .sort_values(["season", "match_number"])
                .groupby("season")
                .tail(1)
                .sort_values("season")
            )

            summary_columns = st.columns(
                len(snapshots)
            )

            for col, (_, row) in zip(
                summary_columns,
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


# ==========================================
# TAB 3 — TEAM COMPARISON
# ==========================================

with compare_tab:
    st.header("Team Comparison")

    st.write(
        "Compare Premier League clubs across season statistics, "
        "points progression, attacking and defensive performance, "
        "and recent form."
    )

    # ======================================
    # SEASON & CLUB SELECTION
    # ======================================

    filter_col, _ = st.columns([1, 2])

    with filter_col:
        comparison_season = st.selectbox(
            "Season",
            SEASONS,
            index=2,
            format_func=lambda s: s.replace("-", "/"),
            key="tc_season",
        )

    season_data = all_results[
        all_results["season"] == comparison_season
    ].copy()

    available_clubs = sorted(
        season_data["team"].unique()
    )

    preferred_clubs = [
        "Manchester United FC",
        "Liverpool FC",
        "Arsenal FC",
    ]

    default_clubs = [
        club for club in preferred_clubs
        if club in available_clubs
    ]

    if len(default_clubs) < 2:
        default_clubs = available_clubs[:2]

    selected_clubs = st.multiselect(
        "Choose clubs (2–4)",
        options=available_clubs,
        default=default_clubs,
        max_selections=4,
        key="tc_clubs",
    )

    if len(selected_clubs) < 2:
        st.info("Select at least two clubs to compare.")

    else:
        comparison_data = season_data[
            season_data["team"].isin(selected_clubs)
        ].copy()

        # Calculate standings using all 20 clubs
        # so league positions remain correct.
        full_standings = build_standings(
            season_data
        ).set_index("team")

        club_colors = {
            club: PALETTE[i % len(PALETTE)]
            for i, club in enumerate(selected_clubs)
        }

        # ==================================
        # 1. SEASON STATISTICS
        # ==================================

        st.divider()

        st.subheader("Season Statistics")

        st.caption(
            "Side-by-side comparison of league statistics "
            "for the selected clubs."
        )

        statistics = {
            "Statistic": [
                "League position",
                "Matches played",
                "Points",
                "Wins",
                "Draws",
                "Losses",
                "Goals scored",
                "Goals conceded",
                "Goal difference",
                "Goals per match",
                "Goals conceded per match",
            ]
        }

        goal_data = []

        for club in selected_clubs:
            club_stats = full_standings.loc[club]

            mp = int(club_stats["MP"])
            gf = int(club_stats["GF"])
            ga = int(club_stats["GA"])

            goals_per_match = gf / mp
            conceded_per_match = ga / mp

            statistics[club] = [
                f"#{int(club_stats['Position'])}",
                mp,
                int(club_stats["Pts"]),
                int(club_stats["W"]),
                int(club_stats["D"]),
                int(club_stats["L"]),
                gf,
                ga,
                int(club_stats["GD"]),
                f"{goals_per_match:.2f}",
                f"{conceded_per_match:.2f}",
            ]

            goal_data.extend([
                {
                    "Club": club,
                    "Metric": "Scored",
                    "Goals per match": goals_per_match,
                },
                {
                    "Club": club,
                    "Metric": "Conceded",
                    "Goals per match": conceded_per_match,
                },
            ])

        statistics_df = pd.DataFrame(statistics)

        st.dataframe(
            statistics_df,
            hide_index=True,
            use_container_width=True,
        )

        st.caption(
            "Goals per match are calculated using completed "
            "league matches. League positions follow SAL's "
            "standings calculation."
        )

        # ==================================
        # 2. POINTS PROGRESSION
        # ==================================

        st.divider()

        st.subheader("Points Progression")

        st.caption(
            "Compare cumulative league points after "
            "each completed match."
        )

        fig_points = px.line(
            comparison_data,
            x="match_number",
            y="cumulative_points",
            color="team",
            markers=True,
            color_discrete_map=club_colors,
            category_orders={
                "team": selected_clubs
            },
            hover_data=[
                "opponent",
                "result",
                "points",
            ],
            labels={
                "match_number": "Matches played",
                "cumulative_points": "Total points",
                "team": "Club",
            },
        )

        fig_points.update_traces(
            line=dict(width=3),
            marker=dict(size=6),
        )

        max_matches = int(
            comparison_data["match_number"].max()
        )

        fig_points.update_xaxes(
            dtick=1 if max_matches <= 10 else 5
        )

        st.plotly_chart(
            style_chart(fig_points, height=460),
            use_container_width=True,
            theme=None,
            key="tc_points_chart",
        )

        st.caption(
            "Comparison is based on matches played, "
            "not calendar dates. Ongoing seasons show "
            "the latest available completed matches."
        )

        # ==================================
        # 3. ATTACK & DEFENSE
        # ==================================

        st.divider()

        st.subheader("Attacking & Defensive Performance")

        st.caption(
            "Average goals scored and conceded per match. "
            "Lower goals conceded indicates a stronger "
            "defensive record."
        )

        goal_comparison = pd.DataFrame(goal_data)

        fig_goals = px.bar(
            goal_comparison,
            x="Goals per match",
            y="Club",
            color="Metric",
            orientation="h",
            barmode="group",
            category_orders={
                "Club": list(reversed(selected_clubs)),
                "Metric": ["Conceded", "Scored"],
            },
            color_discrete_map={
                "Scored": "#2563EB",
                "Conceded": "#F59E0B",
            },
            text_auto=".2f",
        )

        # Keep the legend order: Scored first, Conceded second
        fig_goals.update_traces(
            legendrank=1,
            selector=dict(name="Scored"),
        )

        fig_goals.update_traces(
            legendrank=2,
            selector=dict(name="Conceded"),
        )

        fig_goals.update_layout(
            template="plotly_white",
            height=max(320, len(selected_clubs) * 90),
            margin=dict(
                l=150,
                r=45,
                t=15,
                b=65,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                color="#0F172A",
                size=13,
            ),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.18,
                x=0,
            ),
        )

        fig_goals.update_xaxes(
            gridcolor="rgba(148,163,184,0.20)",
            rangemode="tozero",
        )

        fig_goals.update_yaxes(
            title_text=None,
            automargin=True,
        )

        st.plotly_chart(
            fig_goals,
            use_container_width=True,
            theme=None,
            key="tc_goals_chart",
        )

        
        
        # ==================================
        # 4. FORM TIMELINE
        # ==================================

        st.divider()

        st.subheader("Form Timeline")

        st.caption(
            "Compare match-by-match results across clubs. "
            "W = Win, D = Draw, L = Loss."
        )

        # ==================================
        # MATCH RANGE FILTER
        # ==================================

        # Find the smallest number of completed
        # matches among the selected clubs.
        # This keeps the comparison consistent.

        match_counts = (
            comparison_data
            .groupby("team")["match_number"]
            .max()
        )

        max_common = int(match_counts.min())

        if max_common > 1:

            default_start = max(1, max_common - 4)

            start_match, end_match = st.slider(
                "Select match range",
                min_value=1,
                max_value=max_common,
                value=(default_start, max_common),
                step=1,
                key="tc_form_match_range",
            )

        else:
            start_match = 1
            end_match = 1

            st.caption(
                "Only one completed match is available "
                "for this comparison."
            )

        st.caption(
            f"Comparing matches {start_match}–{end_match} "
            "from each club's completed season record."
        )

        # ==================================
        # FILTER MATCH DATA
        # ==================================

        form_data = comparison_data[
            comparison_data["match_number"].between(
                start_match,
                end_match,
            )
        ].copy()

        form_data = form_data.sort_values(
            ["team", "match_number"]
        )

        # ==================================
        # CHART CONFIGURATION
        # ==================================

        n_clubs = len(selected_clubs)

        fig_form = make_subplots(
            rows=n_clubs,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.10,
            subplot_titles=selected_clubs,
        )

        result_colors = {
            "W": "#16A34A",
            "D": "#94A3B8",
            "L": "#DC2626",
        }

        # Visual heights, NOT actual league points.
        result_heights = {
            "W": 1.0,
            "D": 0.5,
            "L": 0.0,
        }

        form_summary = []

        # ==================================
        # DRAW ONE CHART PER CLUB
        # ==================================

        for row_index, club in enumerate(
            selected_clubs, start=1
        ):

            club_form = form_data[
                form_data["team"] == club
            ].copy()

            # Calculate actual football statistics
            wins = int(
                (club_form["result"] == "W").sum()
            )

            draws = int(
                (club_form["result"] == "D").sum()
            )

            losses = int(
                (club_form["result"] == "L").sum()
            )

            points = int(
                club_form["points"].sum()
            )

            played = len(club_form)

            form_summary.append({
                "Club": club,
                "MP": played,
                "W": wins,
                "D": draws,
                "L": losses,
                "Points": points,
                "Max Points": played * 3,
            })

            # ==================================
            # WIN & DRAW BARS
            # ==================================

            positive = club_form[
                club_form["result"].isin(["W", "D"])
            ].copy()

            positive["bar_height"] = (
                positive["result"].map(result_heights)
            )

            fig_form.add_trace(
                go.Bar(
                    x=positive["match_number"],
                    y=positive["bar_height"],

                    width=0.72,

                    marker=dict(
                        color=[
                            result_colors[result]
                            for result in positive["result"]
                        ],
                        line=dict(width=0),
                    ),

                    # Display W and D inside bars
                    text=positive["result"],
                    textposition="inside",
                    insidetextanchor="middle",

                    textfont=dict(
                        color="#FFFFFF",
                        size=12,
                        family="Arial",
                    ),

                    customdata=positive[
                        [
                            "opponent",
                            "result",
                            "points",
                        ]
                    ].to_numpy(),

                    hovertemplate=(
                        f"<b>{club}</b>"
                        "<br>Match: %{x}"
                        "<br>Opponent: %{customdata[0]}"
                        "<br>Result: %{customdata[1]}"
                        "<br>League points: %{customdata[2]}"
                        "<extra></extra>"
                    ),

                    showlegend=False,
                ),
                row=row_index,
                col=1,
            )

            # ==================================
            # LOSS LABELS AT BASELINE
            # ==================================

            # Losses have zero bar height.
            # Place a red L directly above the
            # baseline so they remain visible.

            lost_matches = club_form[
                club_form["result"] == "L"
            ].copy()

            fig_form.add_trace(
                go.Scatter(
                    x=lost_matches["match_number"],

                    y=[0.02] * len(lost_matches),

                    mode="markers+text",

                    text=["L"] * len(lost_matches),
                    textposition="top center",

                    textfont=dict(
                        color=result_colors["L"],
                        size=13,
                        family="Arial",
                    ),

                    # Invisible markers provide
                    # an interactive hover target.
                    marker=dict(
                        size=14,
                        color="rgba(220,38,38,0)",
                    ),

                    customdata=lost_matches[
                        ["opponent", "result", "points"]
                    ].to_numpy(),

                    hovertemplate=(
                        f"<b>{club}</b>"
                        "<br>Match: %{x}"
                        "<br>Opponent: %{customdata[0]}"
                        "<br>Result: Loss"
                        "<br>League points: 0"
                        "<extra></extra>"
                    ),

                    showlegend=False,
                ),
                row=row_index,
                col=1,
            )

            # ==================================
            # HIDE Y-AXIS
            # ==================================

            fig_form.update_yaxes(
                visible=False,
                range=[-0.08, 1.15],
                showgrid=False,
                zeroline=False,
                fixedrange=True,
                row=row_index,
                col=1,
            )

            # Subtle baseline
            fig_form.add_hline(
                y=0,
                line_width=1,
                line_color="#CBD5E1",
                row=row_index,
                col=1,
            )

        # ==================================
        # X-AXIS — SHOW RANGE ENDPOINTS ONLY
        # ==================================

        axis_ticks = (
            [start_match]
            if start_match == end_match
            else [start_match, end_match]
        )

        fig_form.update_xaxes(
            range=[
                start_match - 0.5,
                end_match + 0.5,
            ],

            tickmode="array",
            tickvals=axis_ticks,

            showgrid=False,
            fixedrange=True,
        )

        fig_form.update_xaxes(
            title_text="Match order",
            row=n_clubs,
            col=1,
        )

        # ==================================
        # CHART STYLING
        # ==================================

        fig_form.update_layout(
            height=165 * n_clubs + 90,

            template="plotly_white",

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",

            margin=dict(
                l=20,
                r=20,
                t=50,
                b=55,
            ),

            font=dict(
                color="#0F172A",
                size=12,
            ),

            barmode="overlay",
            bargap=0.20,

            showlegend=False,
            hovermode="closest",
        )

        st.plotly_chart(
            fig_form,
            use_container_width=True,
            theme=None,
            key="tc_recent_form_compact_bars",
            config={"displayModeBar": False},
        )

        # ==================================
        # CHART EXPLANATION
        # ==================================

        st.caption(
            "Green W = Win (3 points), "
            "Grey D = Draw (1 point), "
            "Red L = Loss (0 points). "
            "Bar heights are visual indicators, "
            "not actual league points."
        )

        # ==================================
        # SELECTED MATCH RANGE SUMMARY
        # ==================================

        st.subheader("Selected Matches Summary")

        summary_df = pd.DataFrame(form_summary)

        summary_df["Points"] = (
            summary_df["Points"].astype(str)
            + " / "
            + summary_df["Max Points"].astype(str)
        )

        st.dataframe(
            summary_df[
                ["Club", "MP", "W", "D", "L", "Points"]
            ],
            hide_index=True,
            use_container_width=True,
        )

        st.caption(
            "Match order refers to each club's "
            "chronological sequence of completed "
            "Premier League fixtures, not official "
            "gameweek numbers."
        )




# ==========================================
# TAB 4 — HEAD-TO-HEAD EXPLORER
# ==========================================

with h2h_tab:
    st.header("Head-to-Head Explorer")

    st.write(
        "Explore previous Premier League meetings "
        "between two clubs."
    )

    # ======================================
    # CLUB SELECTION
    # ======================================

    all_clubs = sorted(
        set(matches["home_team"])
        | set(matches["away_team"])
    )

    col_a, col_b = st.columns(2)

    with col_a:
        default_a = (
            all_clubs.index("Manchester United FC")
            if "Manchester United FC" in all_clubs
            else 0
        )

        team_a = st.selectbox(
            "First club",
            all_clubs,
            index=default_a,
            key="h2h_team_a",
        )

    with col_b:
        available_opponents = [
            club for club in all_clubs
            if club != team_a
        ]

        # Default to Liverpool, regardless
        # of whether the name includes "FC".
        default_b = next(
            (
                i
                for i, club in enumerate(available_opponents)
                if "liverpool" in club.casefold()
            ),
            0,
        )

        team_b = st.selectbox(
            "Second club",
            available_opponents,
            index=default_b,
            key="h2h_team_b",
        )

    # ======================================
    # SEASON FILTER
    # ======================================

    selected_seasons = st.multiselect(
        "Seasons",
        options=SEASONS,
        default=SEASONS,
        format_func=lambda s: s.replace("-", "/"),
        key="h2h_seasons",
    )

    if not selected_seasons:
        st.info("Select at least one season.")

    else:
        # ==================================
        # HEAD-TO-HEAD CALCULATIONS
        # ==================================

        summary, meetings = get_head_to_head(
            matches,
            team_a,
            team_b,
            seasons=selected_seasons,
        )

        if meetings.empty:
            st.info(
                "No completed Premier League meetings "
                "found for these clubs in the "
                "selected seasons."
            )

        else:
            total_matches = summary["matches"]
            team_a_wins = summary["team_a_wins"]
            draws = summary["draws"]
            team_b_wins = summary["team_b_wins"]

            team_a_pct = (team_a_wins / total_matches * 100) if total_matches > 0 else 0
            draw_pct = (draws / total_matches * 100) if total_matches > 0 else 0
            team_b_pct = (team_b_wins / total_matches * 100) if total_matches > 0 else 0

            st.divider()

            st.subheader("Head-to-Head Record")
            st.caption(
                f"{total_matches} completed "
                f"{'meeting' if total_matches == 1 else 'meetings'} "
                "across the selected seasons"
            )
            # ==================================
            # SUMMARY CARDS
            # ==================================
            st.markdown(
                """
                <style>
                .h2h-card {
                    background: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-radius: 16px;
                    padding: 18px 20px;
                    min-height: 130px;
                }
                .h2h-card-title {
                    font-size: 15px;
                    font-weight: 600;
                    color: #0F172A;
                    margin-bottom: 14px;
                }
                .h2h-card-value {
                    font-size: 42px;
                    font-weight: 700;
                    line-height: 1;
                    color: #0F172A;
                    margin-bottom: 10px;
                }
                .h2h-card-subtext {
                    font-size: 14px;
                    color: #64748B;
                }
                .h2h-split-wrap {
                    margin-top: 18px;
                    margin-bottom: 8px;
                }
                .h2h-split-bar {
                    display: flex;
                    width: 100%;
                    height: 24px;
                    border-radius: 999px;
                    overflow: hidden;
                    background: #E2E8F0;
                }
                .h2h-seg-a {
                    background: #2563EB;
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 12px;
                    font-weight: 700;
                }
                .h2h-seg-d {
                    background: #94A3B8;
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 12px;
                    font-weight: 700;
                }
                .h2h-seg-b {
                    background: #F59E0B;
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 12px;
                    font-weight: 700;
                }
                .h2h-legend {
                    display: grid;
                    grid-template-columns: 1fr 1fr 1fr;
                    gap: 12px;
                    margin-top: 10px;
                    margin-bottom: 4px;
                }
                .h2h-legend-item-left {
                    text-align: left;
                    font-size: 14px;
                    color: #334155;
                }
                .h2h-legend-item-center {
                    text-align: center;
                    font-size: 14px;
                    color: #334155;
                }
                .h2h-legend-item-right {
                    text-align: right;
                    font-size: 14px;
                    color: #334155;
                }
                .h2h-dot-a,
                .h2h-dot-d,
                .h2h-dot-b {
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    border-radius: 2px;
                    margin-right: 6px;
                }
                .h2h-dot-a { background: #2563EB; }
                .h2h-dot-d { background: #94A3B8; }
                .h2h-dot-b { background: #F59E0B; }
                </style>
                """,
                unsafe_allow_html=True,
            )

            card_1, card_2, card_3 = st.columns(3)

            with card_1:
                st.markdown(
                    f"""
                    <div class="h2h-card">
                        <div class="h2h-card-title">{team_a}</div>
                        <div class="h2h-card-value">{team_a_wins}</div>
                        <div class="h2h-card-subtext">
                            {team_a_pct:.1f}% • {'win' if team_a_wins == 1 else 'wins'}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with card_2:
                st.markdown(
                    f"""
                    <div class="h2h-card">
                        <div class="h2h-card-title">Draws</div>
                        <div class="h2h-card-value">{draws}</div>
                        <div class="h2h-card-subtext">
                            {draw_pct:.1f}% • {'draw' if draws == 1 else 'draws'}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with card_3:
                st.markdown(
                    f"""
                    <div class="h2h-card">
                        <div class="h2h-card-title">{team_b}</div>
                        <div class="h2h-card-value">{team_b_wins}</div>
                        <div class="h2h-card-subtext">
                            {team_b_pct:.1f}% • {'win' if team_b_wins == 1 else 'wins'}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            
            # ==================================
            # COMPACT RESULT SPLIT BAR
            # ==================================

            team_a_label = (
                f"{team_a_pct:.1f}%"
                if team_a_pct >= 10 else ""
            )
            draw_label = (
                f"{draw_pct:.1f}%"
                if draw_pct >= 10 else ""
            )
            team_b_label = (
                f"{team_b_pct:.1f}%"
                if team_b_pct >= 10 else ""
            )

            # Only render segments that have results.
            # This avoids creating empty 0%-width elements.
            bar_a = (
                f'<div class="h2h-seg-a" '
                f'style="width:{team_a_pct:.2f}%">'
                f'{team_a_label}</div>'
                if team_a_wins > 0 else ""
            )

            bar_d = (
                f'<div class="h2h-seg-d" '
                f'style="width:{draw_pct:.2f}%">'
                f'{draw_label}</div>'
                if draws > 0 else ""
            )

            bar_b = (
                f'<div class="h2h-seg-b" '
                f'style="width:{team_b_pct:.2f}%">'
                f'{team_b_label}</div>'
                if team_b_wins > 0 else ""
            )

            st.html(
                f"""
                <div class="h2h-split-wrap">
                    <div class="h2h-split-bar">
                        {bar_a}
                        {bar_d}
                        {bar_b}
                    </div>

                    <div class="h2h-legend">
                        <div class="h2h-legend-item-left">
                            <span class="h2h-dot-a"></span>
                            {team_a} wins
                        </div>
                        <div class="h2h-legend-item-center">
                            <span class="h2h-dot-d"></span>
                            Draws
                        </div>
                        <div class="h2h-legend-item-right">
                            <span class="h2h-dot-b"></span>
                            {team_b} wins
                        </div>
                    </div>
                </div>
                """
            )


            # ==================================
            # AUTOMATIC INSIGHT
            # ==================================
            if team_a_wins > team_b_wins:
                insight = (
                    f"{team_a} have the better head-to-head record "
                    f"in the selected seasons, with {team_a_wins} wins "
                    f"compared to {team_b_wins} for {team_b}. "
                    f"{draws} meeting(s) ended in draws."
                )
            elif team_b_wins > team_a_wins:
                insight = (
                    f"{team_b} have the better head-to-head record "
                    f"in the selected seasons, with {team_b_wins} wins "
                    f"compared to {team_a_wins} for {team_a}. "
                    f"{draws} meeting(s) ended in draws."
                )
            else:
                insight = (
                    f"Both clubs are level in the selected seasons, "
                    f"with {team_a_wins} win(s) each and {draws} draw(s)."
                )

            st.info(insight)
            
            
            # ==================================
            # PREVIOUS MEETINGS
            # ==================================

            st.divider()

            st.subheader("Previous Meetings")

            display = meetings[
                [
                    "match_date",
                    "season",
                    "home_team",
                    "home_goals",
                    "away_goals",
                    "away_team",
                ]
            ].copy()

            display["Score"] = (
                display["home_goals"].astype(int).astype(str)
                + " - "
                + display["away_goals"].astype(int).astype(str)
            )

            display["match_date"] = (
                pd.to_datetime(display["match_date"])
                .dt.strftime("%d %b %Y")
            )

            display["season"] = (
                display["season"].str.replace(
                    "-", "/", regex=False
                )
            )

            display = display.rename(
                columns={
                    "match_date": "Date",
                    "season": "Season",
                    "home_team": "Home",
                    "away_team": "Away",
                }
            )

            st.dataframe(
                display[
                    ["Date", "Season", "Home", "Score", "Away"]
                ],
                hide_index=True,
                use_container_width=True,
            )

            # ==================================
            # GOALS BREAKDOWN
            # ==================================

            st.divider()

            st.subheader("Goals Breakdown")

            st.caption(
                "Goals scored across the selected "
                "head-to-head meetings."
            )

            # Calculate goals for each club
            # regardless of home or away status.

            team_a_goals = (
                meetings["home_goals"].where(
                    meetings["home_team"] == team_a,
                    meetings["away_goals"],
                ).astype(int)
            )

            team_b_goals = (
                meetings["home_goals"].where(
                    meetings["home_team"] == team_b,
                    meetings["away_goals"],
                ).astype(int)
            )

            total_a_goals = int(team_a_goals.sum())
            total_b_goals = int(team_b_goals.sum())

            total_goals = total_a_goals + total_b_goals
            avg_goals = total_goals / len(meetings)

            goal_a, goal_avg, goal_b = st.columns(3)

            goal_a.metric(
                f"{team_a} Goals",
                total_a_goals,
            )

            goal_avg.metric(
                "Goals per Meeting",
                f"{avg_goals:.2f}",
            )

            goal_b.metric(
                f"{team_b} Goals",
                total_b_goals,
            )

            # ==================================
            # CLEAN SHEETS
            # ==================================

            st.divider()

            st.subheader("Clean Sheets")

            st.caption(
                "Number of meetings in which each "
                "club conceded zero goals."
            )

            team_a_clean_sheets = int(
                (team_b_goals == 0).sum()
            )

            team_b_clean_sheets = int(
                (team_a_goals == 0).sum()
            )

            clean_a, clean_b = st.columns(2)

            clean_a.metric(
                team_a,
                team_a_clean_sheets,
            )

            clean_b.metric(
                team_b,
                team_b_clean_sheets,
            )

            st.caption(
                "Statistics are calculated from completed "
                "Premier League meetings available in "
                "Sports Analytics Lab, not all-time records."
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

