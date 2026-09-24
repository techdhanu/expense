import streamlit as st


# =========================================================
# GLOBAL APP STYLING
# =========================================================

def _inject_global_styles() -> None:
    """
    Inject a shared visual theme (fonts, background, sidebar,
    buttons, links, alerts) used across every page.
    """

    st.markdown(
        """
        <style>

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        .stApp {
            background: linear-gradient(-45deg, #0f172a, #1e293b, #1e1b4b, #0f172a);
            background-size: 400% 400%;
            animation: gradientShift 18s ease infinite;
        }

        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* -----------------------------------------------
           APP HEADER (show_app_header)
        ----------------------------------------------- */

        .app-header {
            padding: 6px 0 18px 0;
            margin-bottom: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }

        .app-title {
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(90deg, #ffffff 0%, #a5b4fc 60%, #818cf8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .app-subtitle {
            margin-top: 4px;
            color: #9ca3af;
            font-size: 0.98rem;
        }

        /* -----------------------------------------------
           SIDEBAR
        ----------------------------------------------- */

        section[data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.85);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
        }

        section[data-testid="stSidebar"] hr {
            margin: 0.9rem 0;
            border-color: rgba(255, 255, 255, 0.08);
        }

        section[data-testid="stSidebar"] .stCaption,
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            background: rgba(99, 102, 241, 0.12);
            border: 1px solid rgba(99, 102, 241, 0.25);
            border-radius: 10px;
            padding: 6px 10px;
            display: inline-block;
        }

        .sidebar-tagline {
            color: #9ca3af;
            font-size: 0.82rem;
            margin: -6px 0 4px 2px;
        }

        .sidebar-section-label {
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            color: #6b7280;
            text-transform: uppercase;
            margin: 4px 0 6px 2px;
        }

        /* Sidebar navigation links */
        section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"],
        section[data-testid="stSidebar"] [data-testid="stPageLink"] {
            border-radius: 10px;
            transition: background 0.2s ease, transform 0.15s ease;
        }

        section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover,
        section[data-testid="stSidebar"] [data-testid="stPageLink"]:hover {
            background: rgba(99, 102, 241, 0.14);
            transform: translateX(2px);
        }

        /* Sidebar logout button gets a danger accent */
        section[data-testid="stSidebar"] div[data-testid="stButton"] button {
            border-radius: 12px;
            border: 1px solid rgba(248, 113, 113, 0.35);
            background: rgba(248, 113, 113, 0.12);
            color: #fca5a5;
            font-weight: 700;
            transition: all 0.2s ease;
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
            background: linear-gradient(135deg, #ef4444, #f87171);
            color: #ffffff;
            border-color: transparent;
            box-shadow: 0 6px 18px rgba(239, 68, 68, 0.35);
            transform: translateY(-1px);
        }

        /* -----------------------------------------------
           GENERIC BUTTONS (non-sidebar)
        ----------------------------------------------- */

        div[data-testid="stButton"] button {
            border-radius: 12px;
            font-weight: 700;
            transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
        }

        div[data-testid="stButton"] button[kind="primary"] {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            border: none;
            box-shadow: 0 6px 18px rgba(99, 102, 241, 0.35);
        }

        div[data-testid="stButton"] button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 24px rgba(99, 102, 241, 0.45);
            filter: brightness(1.08);
        }

        div[data-testid="stButton"] button[kind="secondary"] {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.14);
            color: #e2e8f0;
        }

        div[data-testid="stButton"] button[kind="secondary"]:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.24);
            transform: translateY(-1px);
        }

        div[data-testid="stDownloadButton"] button {
            border-radius: 12px;
            font-weight: 700;
            border: 1px solid rgba(99, 102, 241, 0.35);
            background: rgba(99, 102, 241, 0.10);
            color: #c7d2fe;
            transition: all 0.2s ease;
        }

        div[data-testid="stDownloadButton"] button:hover {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: #ffffff;
            border-color: transparent;
            box-shadow: 0 8px 20px rgba(99, 102, 241, 0.35);
            transform: translateY(-2px);
        }

        /* -----------------------------------------------
           ALERTS
        ----------------------------------------------- */

        div[data-testid="stAlert"] {
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }

        /* -----------------------------------------------
           HEADINGS / DIVIDERS
        ----------------------------------------------- */

        h2, h3 {
            letter-spacing: -0.01em;
        }

        h2 {
            background: linear-gradient(90deg, #ffffff 0%, #c7d2fe 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            display: inline-block;
        }

        hr {
            border-color: rgba(255, 255, 255, 0.08) !important;
            margin: 0.9rem 0 !important;
        }

        /* -----------------------------------------------
           METRIC / KPI CARDS
        ----------------------------------------------- */

        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 16px 18px 12px 18px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        }

        div[data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 28px rgba(99, 102, 241, 0.25);
            border-color: rgba(99, 102, 241, 0.35);
        }

        div[data-testid="stMetricLabel"] {
            color: #9ca3af;
            font-weight: 600;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.6rem;
            font-weight: 800;
            color: #f1f5f9;
        }

        /* -----------------------------------------------
           BORDERED CONTAINERS / FORMS / EXPANDERS
        ----------------------------------------------- */

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 18px !important;
            border-color: rgba(255, 255, 255, 0.10) !important;
            background: rgba(255, 255, 255, 0.03);
            box-shadow: 0 6px 24px rgba(0, 0, 0, 0.25);
            transition: box-shadow 0.2s ease, border-color 0.2s ease;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: rgba(99, 102, 241, 0.30) !important;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.30);
        }

        div[data-testid="stForm"] {
            border-radius: 18px;
            border: 1px solid rgba(255, 255, 255, 0.10);
            background: rgba(255, 255, 255, 0.03);
            box-shadow: 0 6px 24px rgba(0, 0, 0, 0.25);
            padding: 8px 4px;
        }

        div[data-testid="stExpander"] {
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background: rgba(255, 255, 255, 0.02);
        }

        /* -----------------------------------------------
           TEXT INPUTS / TEXTAREA / SELECTBOX / DATE INPUT
        ----------------------------------------------- */

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stDateInput"] input {
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(255, 255, 255, 0.03);
            color: #f1f5f9;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus,
        div[data-testid="stDateInput"] input:focus {
            border-color: #818cf8;
            box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.25);
        }

        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        div[data-testid="stMultiSelect"] > div > div {
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(255, 255, 255, 0.03);
        }

        div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
            background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
            border-radius: 8px;
        }

        div[data-testid="stTextInput"] label,
        div[data-testid="stTextArea"] label,
        div[data-testid="stSelectbox"] label,
        div[data-testid="stDateInput"] label,
        div[data-testid="stMultiSelect"] label {
            font-weight: 600;
            color: #e2e8f0;
            font-size: 0.92rem;
        }

        div[data-testid="stCheckbox"] label {
            color: #cbd5e1;
        }

        /* -----------------------------------------------
           RADIO AS SEGMENTED PILLS
        ----------------------------------------------- */

        div[data-testid="stRadio"] > div {
            gap: 8px;
            background: rgba(255, 255, 255, 0.04);
            padding: 6px;
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }

        div[data-testid="stRadio"] label {
            border-radius: 10px;
            padding: 8px 16px;
            transition: all 0.2s ease;
        }

        div[data-testid="stRadio"] label:has(input:checked) {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.45);
        }

        div[data-testid="stRadio"] label:has(input:checked) p {
            color: #ffffff !important;
            font-weight: 700;
        }

        /* -----------------------------------------------
           TABS (used by login pages)
        ----------------------------------------------- */

        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            background: rgba(255, 255, 255, 0.04);
            padding: 6px;
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.06);
        }

        .stTabs [data-baseweb="tab"] {
            height: 46px;
            border-radius: 10px;
            color: #cbd5e1;
            font-weight: 600;
            transition: all 0.25s ease;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: #ffffff !important;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.45);
        }

        .stTabs [data-baseweb="tab-highlight"] {
            background-color: transparent;
        }

        .stTabs [data-baseweb="tab-border"] {
            display: none;
        }

        /* -----------------------------------------------
           PROGRESS BAR
        ----------------------------------------------- */

        div[data-testid="stProgress"] > div > div {
            background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
            border-radius: 8px;
        }

        div[data-testid="stProgress"] {
            border-radius: 8px;
        }

        /* -----------------------------------------------
           DATAFRAME / PLOTLY CHARTS
        ----------------------------------------------- */

        div[data-testid="stDataFrame"] {
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        }

        div[data-testid="stPlotlyChart"] {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        }

        /* -----------------------------------------------
           FILE UPLOADER
        ----------------------------------------------- */

        div[data-testid="stFileUploader"] section {
            border-radius: 14px;
            border: 1px dashed rgba(255, 255, 255, 0.18);
            background: rgba(255, 255, 255, 0.03);
            transition: border-color 0.2s ease, background 0.2s ease;
        }

        div[data-testid="stFileUploader"] section:hover {
            border-color: rgba(99, 102, 241, 0.45);
            background: rgba(99, 102, 241, 0.06);
        }

        /* -----------------------------------------------
           ACCESSIBILITY: KEYBOARD FOCUS
        ----------------------------------------------- */

        button:focus-visible,
        a:focus-visible,
        input:focus-visible,
        textarea:focus-visible,
        [role="radio"]:focus-visible,
        [role="tab"]:focus-visible,
        div[data-baseweb="select"]:focus-within {
            outline: 2px solid #818cf8 !important;
            outline-offset: 2px;
        }

        /* -----------------------------------------------
           DISABLED CONTROLS
        ----------------------------------------------- */

        div[data-testid="stButton"] button:disabled,
        div[data-testid="stDownloadButton"] button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
            box-shadow: none !important;
        }

        /* -----------------------------------------------
           RESPONSIVE / TABLET BREAKPOINT
        ----------------------------------------------- */

        @media (max-width: 768px) {

            div[data-testid="stMetric"] {
                padding: 14px 16px 10px 16px;
            }

            div[data-testid="stMetricValue"] {
                font-size: 1.4rem;
            }

            .app-title {
                font-size: 1.7rem;
            }
        }

        /* -----------------------------------------------
           RESPONSIVE / MOBILE BREAKPOINT
        ----------------------------------------------- */

        @media (max-width: 640px) {

            div[data-testid="stMetric"] {
                padding: 12px 12px 8px 12px;
                border-radius: 14px;
            }

            div[data-testid="stMetricValue"] {
                font-size: 1.2rem;
            }

            div[data-testid="stPlotlyChart"] {
                padding: 6px;
                border-radius: 12px;
            }

            div[data-testid="stRadio"] > div {
                flex-direction: column;
            }

            div[data-testid="stRadio"] label {
                width: 100%;
                text-align: center;
            }

            .stTabs [data-baseweb="tab"] {
                height: 42px;
                font-size: 0.85rem;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# PAGE SETUP
# =========================================================

def setup_page(
    title: str,
    icon: str = "💰",
    layout: str = "wide",
) -> None:
    """
    Configure common Streamlit page settings.

    Authenticated pages automatically receive
    the application navigation.
    """

    st.set_page_config(
        page_title=f"{icon} {title}",
        page_icon=icon,
        layout=layout,
        initial_sidebar_state="collapsed",
    )

    _inject_global_styles()

    # Show application navigation for authenticated pages.
    if (
        title.lower() != "login"
        and st.session_state.get("authenticated", False)
    ):
        show_sidebar()


# =========================================================
# APP HEADER
# =========================================================

def show_app_header(
    title: str,
    subtitle: str | None = None,
) -> None:
    """Display a consistent application header."""

    subtitle_html = (
        f'<div class="app-subtitle">{subtitle}</div>'
        if subtitle
        else ""
    )

    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-title">{title}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# AUTHENTICATION
# =========================================================

def require_login() -> None:
    """
    Prevent unauthenticated users from accessing
    protected pages.
    """

    if st.session_state.get("authenticated", False):
        return

    st.markdown(
        """
        <div style="
            max-width: 460px;
            margin: 90px auto 24px auto;
            padding: 40px 32px;
            text-align: center;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
            backdrop-filter: blur(14px);
        ">
            <div style="font-size: 64px; line-height: 1;">🔐</div>
            <h2 style="
                margin-top: 14px;
                margin-bottom: 8px;
                background: linear-gradient(90deg, #ffffff 0%, #a5b4fc 60%, #818cf8 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-weight: 800;
            ">Login Required</h2>
            <p style="color: #9ca3af; margin-bottom: 0;">
                Please log in to access your expense tracker.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.page_link(
        "app.py",
        label="🔑 Go to Login",
        icon="🔐",
    )

    st.stop()


# =========================================================
# LOGOUT
# =========================================================

def logout() -> None:
    """Clear authentication-related session state."""

    for key in [
        "authenticated",
        "user_id",
        "username",
    ]:
        st.session_state.pop(
            key,
            None,
        )

    st.switch_page("app.py")


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

def show_sidebar() -> None:
    """Display application navigation in the sidebar."""

    with st.sidebar:

        st.markdown(
            "## 💰 Expense Tracker"
        )

        st.markdown(
            '<div class="sidebar-tagline">Personal Finance</div>',
            unsafe_allow_html=True,
        )

        username = st.session_state.get(
            "username"
        )

        if username:

            st.caption(
                f"Logged in as: **{username}**"
            )

        st.divider()

        # -------------------------------------------------
        # OVERVIEW
        # -------------------------------------------------

        st.markdown(
            '<div class="sidebar-section-label">Overview</div>',
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/Dashboard.py",
            label="Dashboard",
            icon="🏠",
        )

        # -------------------------------------------------
        # MONEY
        # -------------------------------------------------

        st.markdown(
            '<div class="sidebar-section-label">Money</div>',
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/Add_transaction.py",
            label="Add Transaction",
            icon="➕",
        )

        st.page_link(
            "pages/Transaction_History.py",
            label="Transaction History",
            icon="📋",
        )

        st.page_link(
            "pages/accounts.py",
            label="Accounts",
            icon="🏦",
        )

        st.page_link(
            "pages/friends_money.py",
            label="Friends' Money",
            icon="👥",
        )

        # -------------------------------------------------
        # PLANNING
        # -------------------------------------------------

        st.divider()

        st.markdown(
            '<div class="sidebar-section-label">Planning</div>',
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/budgets.py",
            label="Budgets",
            icon="💰",
        )

        st.page_link(
            "pages/savings_goal.py",
            label="Savings Goals",
            icon="🎯",
        )

        st.page_link(
            "pages/recurring_transactions.py",
            label="Recurring Transactions",
            icon="🔄",
        )

        # -------------------------------------------------
        # ANALYTICS
        # -------------------------------------------------

        st.divider()

        st.markdown(
            '<div class="sidebar-section-label">Analytics</div>',
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/reports.py",
            label="Reports",
            icon="📊",
        )

        # -------------------------------------------------
        # SYSTEM
        # -------------------------------------------------

        st.divider()

        st.markdown(
            '<div class="sidebar-section-label">System</div>',
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/backup_restore.py",
            label="Backup & Restore",
            icon="💾",
        )

        st.page_link(
            "pages/settings.py",
            label="Settings",
            icon="⚙️",
        )

        # -------------------------------------------------
        # LOGOUT
        # -------------------------------------------------

        st.divider()

        if st.button(
            "🚪 Logout",
            use_container_width=True,
        ):
            logout()