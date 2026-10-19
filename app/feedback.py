
import streamlit as st
from supabase import create_client


@st.cache_resource
def get_feedback_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_PUBLISHABLE_KEY"],
    )


@st.fragment
def render_feedback(page="general"):
    """Render the SAL product feedback section."""

    sent_key = f"feedback_sent_{page}"

    # ======================================
    # FEEDBACK STYLING
    # ======================================

    st.html("""
    <style>

    /* ========================================
       RATING SIZE TOKENS
       ======================================== */

    :root {
        --sal-star-box: 72px;
        --sal-star-gap: 8px;
        --sal-star-icon: 36px;
    }

    /* ========================================
       RATING CONTAINER
       ======================================== */

    .st-key-sal_feedback_rating_track {
        width: calc(
            5 * var(--sal-star-box) +
            4 * var(--sal-star-gap)
        ) !important;
        max-width: 100% !important;
    }

    /* ========================================
       STAR BUTTONS
       ======================================== */

    .st-key-rating_general [data-testid="stFeedback"]
    [role="radiogroup"] {
        gap: var(--sal-star-gap) !important;
        justify-content: flex-start !important;
    }

    .st-key-rating_general [data-testid="stFeedback"]
    button {
        width: var(--sal-star-box) !important;
        min-width: var(--sal-star-box) !important;
        height: var(--sal-star-box) !important;
        flex: 0 0 var(--sal-star-box) !important;

        padding: 10px !important;
        background-color: #F1F5F9 !important;
        border-radius: 10px !important;

        transition: background-color 0.15s ease;
    }

    .st-key-rating_general [data-testid="stFeedback"]
    button:hover {
        background-color: #E2E8F0 !important;
    }

    .st-key-rating_general [data-testid="stFeedback"]
    button span {
        font-size: var(--sal-star-icon) !important;
    }

    .st-key-rating_general [data-testid="stFeedback"]
    button img,
    .st-key-rating_general [data-testid="stFeedback"]
    button svg {
        width: var(--sal-star-icon) !important;
        height: var(--sal-star-icon) !important;
    }

    /* ========================================
       RATING SCALE LABELS
       ======================================== */

    .sal-rating-scale {
        display: flex;
        justify-content: space-between;
        width: 100%;
        color: #64748B;
        font-size: 13px;
        margin-top: 6px;
    }

    /* ========================================
       MOBILE RESPONSIVENESS
       ======================================== */

    @media (max-width: 768px) {

        :root {
            --sal-star-box: clamp(44px, 14vw, 60px);
            --sal-star-gap: 8px;
            --sal-star-icon: clamp(24px, 7vw, 28px);
        }

        .st-key-sal_feedback_rating_track {
            margin-left: auto !important;
            margin-right: auto !important;
        }
    }


    /* ========================================
    RESPONSIVE FEEDBACK LAYOUT
    ======================================== */

    /* Stack columns on tablets and narrower screens */
    @media (max-width: 1400px) {

        .st-key-sal_feedback_layout
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 1.5rem !important;
        }

        .st-key-sal_feedback_layout
        [data-testid="stColumn"] {
            flex: none !important;
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
        }

        /* Center stars and labels together */
        .st-key-sal_feedback_rating_track {
            margin-left: auto !important;
            margin-right: auto !important;
        }
    }


    </style>
    """)

    # ======================================
    # SECTION HEADER
    # ======================================

    st.subheader("Help improve Sports Analytics Lab")

    st.caption(
        "Share your experience and help shape "
        "future improvements."
    )

    if st.session_state.get(sent_key, False):
        st.success("Thank you for your feedback!")
        return

    # ======================================
    # FEEDBACK INPUTS
    # ======================================

    feedback_layout = st.container(
        key="sal_feedback_layout",
        border=False
    )

    rating_col, comment_col = feedback_layout.columns(
        [1, 2.25],
        gap="small"
    )

    with rating_col:
        st.markdown(
            "**How would you rate your experience?**"
        )

        # Keep the stars and scale labels aligned
        with st.container(
            key="sal_feedback_rating_track",
            border=False,
            gap="xxsmall"
        ):
            rating = st.feedback(
                "stars",
                key=f"rating_{page}"
            )

            st.html("""
            <div class="sal-rating-scale">
                <span>Poor</span>
                <span>Excellent</span>
            </div>
            """)

    # ======================================
    # COMMENT INPUT
    # ======================================

    with comment_col:
        comment = st.text_area(
            "Tell us more about your experience",
            placeholder=(
                "What works well? "
                "What should we improve?"
            ),
            max_chars=1000,
            height=110,
            key=f"comment_{page}"
        )

        submitted = st.button(
            "Submit feedback",
            key=f"submit_{page}",
            type="primary"
        )

    # ======================================
    # FEEDBACK SUBMISSION
    # ======================================

    if submitted:
        if rating is None and not comment.strip():
            st.warning(
                "Please provide a rating or comment."
            )
            return

        try:
            get_feedback_client().table(
                "product_feedback"
            ).insert(
                {
                    "page": page,
                    "app_version": "v0.2.1",
                    "rating": (
                        rating + 1
                        if rating is not None
                        else None
                    ),
                    "comment": comment.strip() or None,
                },
                returning="minimal"
            ).execute()

            st.session_state[sent_key] = True
            st.rerun(scope="fragment")

        except Exception:
            st.error(
                "Unable to submit feedback. "
                "Please try again."
            )
