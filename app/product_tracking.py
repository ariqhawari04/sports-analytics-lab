
import logging
from uuid import uuid4

import streamlit as st
from supabase import create_client


logger = logging.getLogger(__name__)


@st.cache_resource
def get_tracking_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_PUBLISHABLE_KEY"],
    )


def track_event(event_name, page=None):
    """Insert a product analytics event into Supabase."""

    try:
        get_tracking_client().table(
            "product_events"
        ).insert(
            {
                "session_id": st.session_state["sal_session_id"],
                "event_name": event_name,
                "page": page,
                "app_version": "v0.2.2",
            },
            returning="minimal"
        ).execute()

        return True

    except Exception:
        logger.exception("Product event tracking failed")
        return False


def initialize_session_tracking():
    """Create a session ID and log its first event."""

    if "sal_session_id" not in st.session_state:
        st.session_state["sal_session_id"] = str(uuid4())

    if not st.session_state.get("sal_session_logged", False):
        if track_event("session_start"):
            st.session_state["sal_session_logged"] = True


def track_active_tab(page):
    """Track actual tab changes, not ordinary widget reruns."""

    if st.session_state.get("sal_last_tab") == page:
        return

    if track_event("tab_view", page=page):
        st.session_state["sal_last_tab"] = page
