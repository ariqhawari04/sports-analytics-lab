import os
import logging
from pathlib import Path
from html import escape

import pandas as pd
import plotly.express as px
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

from datetime import datetime, time as dt_time, timedelta, timezone
from zoneinfo import ZoneInfo

import hashlib
import hmac
import time

import streamlit as st


# ==========================================
# SAL v0.2.3 - ADMIN ACCESS
# ==========================================

st.set_page_config(
    page_title="Staff Access | Sports Analytics Lab",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300
SESSION_SECONDS = 1800


# ==========================================
# STAFF ACCESS — SHARED STYLING
# ==========================================

st.markdown(
    """
<style>



/* ==========================================
   SHARED PAGE LAYOUT
   ========================================== */

/* Same layout as the public SAL app */
.block-container {
    max-width: 1750px !important;
    padding: 2rem 2.5rem 3.5rem !important;
}

@media (max-width: 768px) {
    .block-container {
        padding: 1.4rem 1rem 2rem !important;
    }
}




/* Shared topbar for login and dashboard */

.st-key-sal_admin_topbar {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem;
    margin-bottom: 1.2rem;
    border-bottom: 1px solid #E2E8F0;
}


.st-key-sal_admin_signout button {
    border-radius: 10px;
    font-weight: 600;
}



/* SAL brand */
.sal-admin-brand {
    color: #0F172A;
    font-size: clamp(1.8rem, 2.8vw, 2.65rem);
    font-weight: 800;
    letter-spacing: -0.05em;
    line-height: 1.15;
}

.sal-admin-brand span {
    color: #2563EB;
}

/* Login page topbar */
.sal-login-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 1rem;

    border-bottom: 1px solid #E2E8F0;
    padding: 0.5rem 0 1.25rem;
    margin-bottom: 3rem;
}

.sal-login-context {
    color: #64748B;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.12em;
}

/* Login introduction */
.sal-login-intro {
    text-align: center;
    margin-bottom: 1.5rem;
}

.sal-login-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    border-radius: 14px;
    background: #EFF6FF;
    color: #2563EB;
    margin-bottom: 1rem;
}

.sal-login-intro h1 {
    color: #0F172A;
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    margin: 0 0 0.65rem;
}

.sal-login-intro p {
    color: #64748B;
    font-size: 0.95rem;
    line-height: 1.6;
    margin: 0;
}

/* Existing login form */
.st-key-sal_admin_login {
    background: #FFFFFF !important;
    border: 1px solid #DCE4ED !important;
    border-radius: 16px !important;
    padding: 1.4rem !important;
}

.st-key-sal_admin_login button {
    border-radius: 10px !important;
    font-weight: 600 !important;
}

@media (max-width: 650px) {
    .sal-login-topbar {
        margin-bottom: 2rem;
    }

    .sal-admin-brand {
        font-size: 1.75rem;
    }

    .sal-login-intro h1 {
        font-size: 1.65rem;
    }

    .st-key-sal_admin_login {
        padding: 1rem !important;
    }
}


</style>
    """,
    unsafe_allow_html=True,
)


def verify_admin_password(password: str) -> bool:
    """Verify password against the stored PBKDF2 hash."""

    if len(password.encode("utf-8")) > 256:
        return False

    salt = bytes.fromhex(st.secrets["admin"]["salt"])

    expected_hash = bytes.fromhex(
        st.secrets["admin"]["password_hash"]
    )

    submitted_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000,
    )

    return hmac.compare_digest(
        submitted_hash,
        expected_hash,
    )


def require_admin():
    """Stop rendering until admin access is verified."""

    now = time.time()

    # Existing authenticated session
    if st.session_state.get("sal_admin_authenticated", False):

        authenticated_at = st.session_state.get(
            "sal_admin_authenticated_at", 0
        )

        if now - authenticated_at < SESSION_SECONDS:
            return

        st.session_state.pop(
            "sal_admin_authenticated", None
        )
        st.session_state.pop(
            "sal_admin_authenticated_at", None
        )

        st.warning("Your admin session has expired.")

    
    # ==========================================
    # LOGIN SCREEN
    # ==========================================

    _, middle, _ = st.columns([1, 1.4, 1])


    with middle:
        
        st.html("""
        <div class="sal-login-intro">
            <div class="sal-login-icon">
                &#128274;
            </div>

            <h1>Staff Access</h1>

            <p>
                Sign in to access internal product
                analytics and feedback insights.
            </p>
        </div>
        """)


        locked_until = st.session_state.get(
            "sal_admin_locked_until", 0
        )

        if now < locked_until:
            st.error(
                "Too many failed attempts. "
                "Please try again later."
            )
            st.stop()

        
        with st.form(
            "sal_admin_login",
            clear_on_submit=True,
        ):
            password = st.text_input(
                "Admin password",
                type="password",
                autocomplete="current-password",
            )

            submitted = st.form_submit_button(
                "Unlock dashboard",
                use_container_width=True,
                type="primary",
            )


        if submitted:
            try:
                valid = verify_admin_password(password)
            except (KeyError, FileNotFoundError, ValueError):
                st.error(
                    "Admin credentials are not configured."
                )
                st.stop()

            if valid:
                st.session_state[
                    "sal_admin_authenticated"
                ] = True

                st.session_state[
                    "sal_admin_authenticated_at"
                ] = time.time()

                st.session_state[
                    "sal_admin_failures"
                ] = 0

                st.session_state.pop(
                    "sal_admin_locked_until", None
                )

                
                st.rerun()

            else:
                failures = st.session_state.get(
                    "sal_admin_failures", 0
                ) + 1

                if failures >= MAX_ATTEMPTS:
                    st.session_state[
                        "sal_admin_locked_until"
                    ] = time.time() + LOCKOUT_SECONDS

                    st.session_state[
                        "sal_admin_failures"
                    ] = 0

                    st.error(
                        "Too many failed attempts. "
                        "Access temporarily locked."
                    )

                else:
                    st.session_state[
                        "sal_admin_failures"
                    ] = failures

                    st.error("Incorrect password.")

    # Never render protected content before authentication
    st.stop()



# ==========================================
# SHARED SAL HEADER
# ==========================================

is_admin_active = (
    st.session_state.get("sal_admin_authenticated", False)
    and time.time()
    - st.session_state.get("sal_admin_authenticated_at", 0)
    < SESSION_SECONDS
)

with st.container(key="sal_admin_topbar"):

    brand_col, action_col = st.columns(
        [5, 1],
        vertical_alignment="center",
    )

    with brand_col:
        st.html("""
        <div class="sal-admin-brand">
            Sports Analytics Lab<span>.</span>
        </div>
        """)

    with action_col:
        if is_admin_active:
            if st.button(
                "Sign out",
                key="sal_admin_signout",
                use_container_width=True,
            ):
                st.session_state.pop(
                    "sal_admin_authenticated", None
                )
                st.session_state.pop(
                    "sal_admin_authenticated_at", None
                )
                st.rerun()
        else:
            st.html("""
            <div class="sal-login-context"
                 style="text-align: right;">
                INTERNAL ACCESS
            </div>
            """)


# ==========================================
# PROTECTED ADMIN CONTENT
# ==========================================

require_admin()


# ==========================================
# PRODUCT ANALYTICS — DATA ACCESS
# ==========================================

logger = logging.getLogger(__name__)



def load_analytics_overview(start_utc, end_utc):
    """Read analytics for the selected date range."""

    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")

    host = (
        os.getenv("SUPABASE_POOLER_HOST")
        or st.secrets["SUPABASE_POOLER_HOST"]
    )

    date_params = (start_utc, end_utc)

    with psycopg.connect(
        host=host,
        port=5432,
        dbname="postgres",
        user=st.secrets["analytics_db"]["user"],
        password=st.secrets["analytics_db"]["password"],
        sslmode="require",
        connect_timeout=15,
        row_factory=dict_row,
    ) as conn:

        with conn.cursor() as cursor:

            # Selected-period traffic summary
            cursor.execute("""
                SELECT
                    COUNT(*) FILTER (
                        WHERE event_name = 'session_start'
                    ) AS total_sessions,

                    COUNT(*) FILTER (
                        WHERE event_name = 'tab_view'
                    ) AS total_feature_views

                FROM public.product_events

                WHERE created_at >= %s
                  AND created_at < %s
            """, date_params)

            overview = cursor.fetchone()

            # Daily session and feature activity
            cursor.execute("""
                SELECT
                    (
                        created_at AT TIME ZONE 'Asia/Jakarta'
                    )::DATE AS activity_date,

                    COUNT(*) FILTER (
                        WHERE event_name = 'session_start'
                    ) AS total_sessions,

                    COUNT(*) FILTER (
                        WHERE event_name = 'tab_view'
                    ) AS total_feature_views

                FROM public.product_events

                WHERE created_at >= %s
                  AND created_at < %s

                GROUP BY activity_date
                ORDER BY activity_date
            """, date_params)

            daily = cursor.fetchall()

            # Feature engagement
            cursor.execute("""
                SELECT
                    page AS feature,
                    COUNT(*) AS total_views,
                    COUNT(DISTINCT session_id)
                        AS sessions_reached

                FROM public.product_events

                WHERE event_name = 'tab_view'
                  AND created_at >= %s
                  AND created_at < %s

                GROUP BY page
                ORDER BY total_views DESC
            """, date_params)

            features = cursor.fetchall()

            # Feedback summary
            cursor.execute("""
                SELECT
                    COUNT(*) AS total_submissions,
                    COUNT(rating) AS total_ratings,
                    ROUND(AVG(rating)::NUMERIC, 2)
                        AS average_rating

                FROM public.product_feedback

                WHERE created_at >= %s
                  AND created_at < %s
            """, date_params)

            feedback_summary = cursor.fetchone()

            # Rating distribution
            cursor.execute("""
                SELECT
                    rating,
                    COUNT(*) AS submissions

                FROM public.product_feedback

                WHERE rating IS NOT NULL
                  AND created_at >= %s
                  AND created_at < %s

                GROUP BY rating
                ORDER BY rating
            """, date_params)

            ratings = cursor.fetchall()

            # Recent comments within selected dates
            cursor.execute("""
                SELECT
                    (
                        created_at AT TIME ZONE 'Asia/Jakarta'
                    ) AS submitted_at_wib,
                    rating,
                    comment

                FROM public.product_feedback

                WHERE NULLIF(BTRIM(comment), '') IS NOT NULL
                  AND created_at >= %s
                  AND created_at < %s

                ORDER BY created_at DESC
                LIMIT 20
            """, date_params)

            comments = cursor.fetchall()

    return (
        overview,
        pd.DataFrame(daily),
        pd.DataFrame(features),
        feedback_summary,
        pd.DataFrame(ratings),
        pd.DataFrame(comments),
    )





# ==========================================
# SAL v0.2.3 — INTERNAL DASHBOARD UI
# ==========================================

st.html("""
<style>

.sal-admin-eyebrow {
    color: #2563EB;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    margin-bottom: 0.55rem;
}

.sal-admin-title {
    color: #0F172A;
    font-size: clamp(2rem, 3vw, 2.8rem);
    font-weight: 800;
    letter-spacing: -0.045em;
    line-height: 1.15;
    margin: 0;
}

.sal-admin-subtitle {
    color: #64748B;
    font-size: 0.95rem;
    margin-top: 0.7rem;
}

.st-key-sal_admin_kpis [data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #DCE4ED;
    border-radius: 14px;
    padding: 1.2rem;
    min-height: 125px;
}

.st-key-sal_admin_traffic_card,
.st-key-sal_admin_feature_card,
.st-key-sal_admin_rating_card,
.st-key-sal_admin_comments_card {
    background: #FFFFFF !important;
    border: 1px solid #DCE4ED !important;
    border-radius: 16px !important;
    padding: 1.1rem !important;
}


/* ==========================================
   SAL BRAND HEADER
   ========================================== */

@media (max-width: 768px) {
    .sal-admin-brand {
        font-size: 1.75rem;
    }
}
</style>
""")



# ==========================================
# DASHBOARD HEADING & DATE FILTER
# ==========================================

title_col, filter_col = st.columns(
    [3, 2],
    gap="large",
    vertical_alignment="bottom",
)

with title_col:
    st.markdown("## Product Analytics")

    st.caption(
        "Understand traffic, engagement, "
        "and user feedback."
    )

with filter_col:
    wib = ZoneInfo("Asia/Jakarta")
    today_wib = datetime.now(wib).date()

    selected_range = st.date_input(
        "Date range (WIB)",
        value=(
            today_wib - timedelta(days=29),
            today_wib,
        ),
        max_value=today_wib,
        format="DD/MM/YYYY",
        key="sal_admin_date_range",
    )


# Wait until both dates are selected.
if not isinstance(selected_range, tuple) or len(selected_range) != 2:
    st.info("Please select a start and end date.")
    st.stop()

start_date, end_date = selected_range

# Convert inclusive WIB dates to an exclusive
# UTC timestamp range for PostgreSQL.
start_utc = datetime.combine(
    start_date,
    dt_time.min,
    tzinfo=wib,
).astimezone(timezone.utc)

end_utc = datetime.combine(
    end_date + timedelta(days=1),
    dt_time.min,
    tzinfo=wib,
).astimezone(timezone.utc)


# ==========================================
# LOAD ANALYTICS DATA
# ==========================================

try:
    (
        overview,
        daily,
        features,
        feedback_summary,
        ratings,
        comments,
    ) = load_analytics_overview(
        start_utc,
        end_utc,
    )

except Exception:
    logger.exception("Failed to load SAL product analytics")
    st.error(
        "Unable to load analytics data. "
        "Please check the server logs."
    )
    st.stop()


total_sessions = int(overview["total_sessions"])
total_views = int(overview["total_feature_views"])

views_per_session = (
    total_views / total_sessions
    if total_sessions > 0 else 0
)

total_submissions = int(
    feedback_summary["total_submissions"]
)

total_ratings = int(
    feedback_summary["total_ratings"]
)

average_rating = feedback_summary["average_rating"]

st.space("medium")


# ==========================================
# KPI OVERVIEW
# ==========================================

st.markdown("### Overview")

with st.container(key="sal_admin_kpis"):
    kpi1, kpi2, kpi3, kpi4 = st.columns(
        4, gap="small"
    )

    with kpi1:
        st.metric(
            "Recorded Sessions",
            f"{total_sessions:,}",
        )

    with kpi2:
        st.metric(
            "Feature Views",
            f"{total_views:,}",
        )

    with kpi3:
        st.metric(
            "Views / Session",
            f"{views_per_session:.2f}",
        )

    with kpi4:
        st.metric(
            "Feedback Submissions",
            f"{total_submissions:,}",
        )


# ==========================================
# ACTIVITY & ENGAGEMENT
# ==========================================

st.space("medium")
st.markdown("### Activity & Engagement")

traffic_col, feature_col = st.columns(
    2, gap="medium"
)


# ----- DAILY SESSIONS -----

with traffic_col:
    with st.container(
        border=True,
        key="sal_admin_traffic_card",
    ):
        st.markdown("#### Daily Sessions")
        st.caption("Recorded sessions · WIB")

        if daily.empty:
            st.caption("No traffic data available.")

        else:
            daily_plot = daily.copy()

            daily_plot["activity_date"] = (
                pd.to_datetime(
                    daily_plot["activity_date"]
                ).dt.normalize()
            )

            # Include zero-activity days between
            # the first available date and today.
            date_range = pd.date_range(
                start=start_date,
                end=end_date,
                freq="D",
            )

            daily_plot = (
                daily_plot
                .groupby("activity_date")["total_sessions"]
                .sum()
                .reindex(date_range, fill_value=0)
                .rename_axis("activity_date")
                .reset_index()
            )

            
            fig_daily = px.line(
                daily_plot,
                x="activity_date",
                y="total_sessions",
                markers=True,
            )

            fig_daily.update_traces(
                line=dict(
                    color="#2563EB",
                    width=3.5,
                    shape="linear",
                ),
                marker=dict(
                    size=7,
                    color="#2563EB",
                    line=dict(
                        color="#F8FAFC",
                        width=2,
                    ),
                ),
                fill="tozeroy",
                fillcolor="rgba(37,99,235,0.09)",
                hovertemplate=(
                    "%{x|%d %b %Y}<br>"
                    "%{y} sessions<extra></extra>"
                ),
            )

            fig_daily.update_layout(
                template="plotly_white",
                height=320,
                font=dict(
                    size=13,
                    color="#0F172A",
                    family="Arial",
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(
                    l=10, r=15, t=20, b=30
                ),
                hovermode="x unified",
                showlegend=False,
                xaxis_title=None,
                yaxis_title="Sessions",
            )

            fig_daily.update_xaxes(
                showgrid=False,
                linecolor="#CBD5E1",
                tickformat="%d %b",
                nticks=5,
            )

            fig_daily.update_yaxes(
                gridcolor="rgba(148,163,184,0.20)",
                griddash="dot",
                zeroline=False,
                rangemode="tozero",
            )

            st.plotly_chart(
                fig_daily,
                width="stretch",
                theme=None,
                config={"displayModeBar": False},
            )



# ----- FEATURE ENGAGEMENT -----

with feature_col:
    with st.container(
        border=True,
        key="sal_admin_feature_card",
    ):
        st.markdown("#### Feature Engagement")
        st.caption("Total recorded tab views")

        if features.empty:
            st.caption("No feature activity available.")

        else:
            feature_labels = {
                "league_overview": "League Overview",
                "team_explorer": "Team Explorer",
                "team_comparison": "Team Comparison",
                "head_to_head": "Head-to-Head",
            }

            feature_plot = features.copy()

            feature_plot["feature_name"] = (
                feature_plot["feature"]
                .map(feature_labels)
                .fillna(feature_plot["feature"])
            )

            feature_plot = feature_plot.sort_values(
                "total_views",
                ascending=True,
            )

            fig_features = px.bar(
                feature_plot,
                x="total_views",
                y="feature_name",
                orientation="h",
                text="total_views",
            )

            fig_features.update_traces(
                marker_color="#2563EB",
                textposition="outside",
                cliponaxis=False,
            )

            
            fig_features.update_layout(
                template="plotly_white",
                height=320,
                font=dict(
                    size=13,
                    color="#0F172A",
                    family="Arial",
                ),
                showlegend=False,
                margin=dict(
                    l=10, r=35, t=15, b=30
                ),
                xaxis_title="Feature Views",
                yaxis_title=None,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )

            fig_features.update_xaxes(
                gridcolor="rgba(148,163,184,0.20)",
                griddash="dot",
                rangemode="tozero",
                zeroline=False,
            )

            fig_features.update_yaxes(
                showgrid=False,
            )

            st.plotly_chart(
                fig_features,
                width="stretch",
                config={"displayModeBar": False},
            )


# ==========================================
# USER FEEDBACK
# ==========================================

st.space("medium")
st.markdown("### User Feedback")

feedback_kpi1, feedback_kpi2 = st.columns(2)

with feedback_kpi1:
    st.metric(
        "Ratings Received",
        f"{total_ratings:,}",
    )

with feedback_kpi2:
    st.metric(
        "Average Rating",
        (
            f"{float(average_rating):.2f} / 5"
            if average_rating is not None
            else "—"
        ),
    )


rating_col, comment_col = st.columns(
    [1, 1.3],
    gap="medium",
)


# ----- RATING DISTRIBUTION -----

with rating_col:
    with st.container(
        border=True,
        key="sal_admin_rating_card",
    ):
        st.markdown("#### Rating Distribution")

        if total_ratings == 0:
            st.caption(
                "No ratings yet. New submissions "
                "will appear here."
            )

        else:
            rating_scale = pd.DataFrame({
                "rating": [1, 2, 3, 4, 5]
            })

            rating_plot = rating_scale.merge(
                ratings,
                on="rating",
                how="left",
            )

            rating_plot["submissions"] = (
                rating_plot["submissions"]
                .fillna(0)
                .astype(int)
            )

            fig_ratings = px.bar(
                rating_plot,
                x="rating",
                y="submissions",
                text="submissions",
            )

            fig_ratings.update_traces(
                marker_color="#2563EB",
                textposition="outside",
                cliponaxis=False,
            )

            
            fig_ratings.update_layout(
                template="plotly_white",
                height=300,
                font=dict(
                    size=13,
                    color="#0F172A",
                    family="Arial",
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                bargap=0.35,
                margin=dict(
                    l=10,
                    r=15,
                    t=25,
                    b=30,
                ),
                xaxis_title="Stars",
                yaxis_title="Submissions",
            )

            fig_ratings.update_xaxes(
                tickmode="array",
                tickvals=[1, 2, 3, 4, 5],
                showgrid=False,
                linecolor="#CBD5E1",
            )

            fig_ratings.update_yaxes(
                gridcolor="rgba(148,163,184,0.20)",
                griddash="dot",
                zeroline=False,
                rangemode="tozero",
                tickformat="d",
            )

            # Avoid fractional count labels
            # when there are only a few ratings.
            if rating_plot["submissions"].max() <= 10:
                fig_ratings.update_yaxes(dtick=1)

            st.plotly_chart(
                fig_ratings,
                width="stretch",
                theme=None,
                config={"displayModeBar": False},
            )



# ----- RECENT COMMENTS -----

with comment_col:
    with st.container(
        border=True,
        key="sal_admin_comments_card",
    ):
        st.markdown("#### Recent Comments")
        st.caption("Latest 20 written submissions")

        if comments.empty:
            st.caption(
                "No written feedback yet. "
                "New comments will appear here."
            )

        
        
        else:
            # ======================================
            # BUILD COMMENT TABLE ROWS
            # ======================================

            rows_html = []

            for item in comments.itertuples(index=False):

                submitted = pd.to_datetime(
                    item.submitted_at_wib
                ).strftime("%d %b %Y, %H:%M")

                rating_text = (
                    f"{int(item.rating)} / 5"
                    if pd.notna(item.rating)
                    else "—"
                )

                comment_text = escape(str(item.comment))

                
                rows_html.append(f"""
                    <tr>
                        <td>{escape(submitted)}</td>
                        <td class="sal-comment-rating">{escape(rating_text)}</td>
                        <td class="sal-comment-text">{comment_text}</td>
                    </tr>
                """)


            table_rows = "\n".join(rows_html)

            # ======================================
            # TABLE STYLING
            # ======================================

            table_css = """
            <style>

            .sal-comments-scroll {
                width: 100%;
                overflow-x: auto;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                background: #FFFFFF;
            }

            .sal-comments-table {
                width: 100%;
                min-width: 520px;
                border-collapse: separate;
                border-spacing: 0;
                table-layout: fixed;
                font-size: 13px;
                color: #0F172A;
            }

            .sal-comments-table th,
            .sal-comments-table td {
                padding: 10px 12px !important;
                text-align: left !important;
                vertical-align: middle !important;
                line-height: 1.4 !important;
                height: auto !important;
                border-bottom: 1px solid #EDF2F7;
            }

            .sal-comments-table thead th {
                background: #F1F5F9 !important;
                color: #64748B !important;
                font-weight: 600 !important;
                white-space: nowrap;
            }

            .sal-comments-table tbody td {
                background: #FFFFFF !important;
                color: #0F172A !important;
            }

            .sal-comments-table tbody tr:hover td {
                background: #F8FAFC !important;
            }

            .sal-comments-table tbody tr:last-child td {
                border-bottom: none;
            }

            .sal-comments-table th:nth-child(1) {
                width: 33%;
            }

            .sal-comments-table th:nth-child(2) {
                width: 17%;
            }

            .sal-comments-table th:nth-child(3) {
                width: 50%;
            }

            .sal-comments-table td:first-child {
                white-space: nowrap;
            }

            .sal-comments-table .sal-comment-rating {
                color: #2563EB !important;
                font-weight: 700;
                white-space: nowrap;
            }

            .sal-comments-table .sal-comment-text {
                text-align: left !important;
                white-space: pre-line;
                overflow-wrap: anywhere;
            }

            </style>
            """

            # ======================================
            # RENDER TABLE
            # ======================================

            table_html = f"""
            <div class="sal-comments-scroll">
                <table class="sal-comments-table">
                    <thead>
                        <tr>
                            <th>Submitted (WIB)</th>
                            <th>Rating</th>
                            <th>Comment</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            """

            st.html(table_css + table_html)




# ==========================================
# DASHBOARD FOOTER
# ==========================================

st.space("small")

st.caption(
    "Sports Analytics Lab · Internal Product Analytics · "
    "All timestamps use Asia/Jakarta (WIB). "
    "Sessions are not unique visitors."
)
