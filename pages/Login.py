import streamlit as st

from components.navigation import setup_page
from services.authentication_service import authenticate_user, create_user


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

setup_page(
    title="Login",
    icon="🔐",
    layout="centered",
)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = None


# ---------------------------------------------------------
# IF ALREADY LOGGED IN
# ---------------------------------------------------------

if st.session_state.get("authenticated", False):
    st.switch_page("pages/Dashboard.py")


# ---------------------------------------------------------
# CUSTOM LOGIN UI
# ---------------------------------------------------------

st.markdown(
    """
    <style>

    /* ---------------------------------------------------
       Shared theme (fonts, background, buttons, tabs,
       inputs, alerts) already comes from setup_page().
       Only the classes unique to this login layout live
       here.
    --------------------------------------------------- */

    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 3rem;
        max-width: 560px;
    }

    .login-container {
        max-width: 480px;
        margin: 40px auto 0 auto;
        padding: 28px 26px 18px 26px;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        animation: fadeInUp 0.6s ease;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(18px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .login-logo {
        text-align: center;
        font-size: 64px;
        margin-bottom: 10px;
        filter: drop-shadow(0 6px 18px rgba(99, 102, 241, 0.45));
    }

    .login-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 5px;
        background: linear-gradient(90deg, #ffffff 0%, #a5b4fc 60%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
    }

    .login-subtitle {
        text-align: center;
        color: #9ca3af;
        margin-bottom: 30px;
        font-size: 1rem;
    }

    .stCaption, [data-testid="stCaptionContainer"] {
        text-align: center;
    }

    /* -------------------------------------------------
       RESPONSIVE / MOBILE FRIENDLY
    ------------------------------------------------- */

    @media (max-width: 480px) {

        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 1.2rem;
        }

        .login-container {
            padding: 20px 14px 12px 14px;
            border-radius: 16px;
        }

        .login-logo {
            font-size: 52px;
        }

        .login-title {
            font-size: 1.9rem;
        }

        .login-subtitle {
            font-size: 0.9rem;
            margin-bottom: 20px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    '<div class="login-container">',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="login-logo">💰</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="login-title">Expense Tracker</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="login-subtitle">'
    'Manage your money simply and securely.'
    '</div>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# LOGIN / CREATE ACCOUNT TABS
# ---------------------------------------------------------

login_tab, create_tab = st.tabs(
    [
        "🔐 Login",
        "👤 Create Account",
    ]
)


# =========================================================
# LOGIN
# =========================================================

with login_tab:

    st.markdown("### Welcome back 👋")

    username = st.text_input(
        "Username",
        placeholder="Enter your username",
        key="login_username",
    )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
        key="login_password",
    )

    st.caption(
        "Enter the username and password you used when creating your account."
    )

    if st.button(
        "🔐 Login",
        use_container_width=True,
        type="primary",
    ):

        if not username.strip():
            st.error("Please enter your username.")

        elif not password:
            st.error("Please enter your password.")

        else:

            try:

                user = authenticate_user(
                    username.strip(),
                    password,
                )

                if user:

                    st.session_state.authenticated = True
                    st.session_state.user_id = user["id"]
                    st.session_state.username = user["username"]

                    st.success("Login successful!")

                    st.switch_page(
                        "pages/Dashboard.py"
                    )

                else:

                    st.error(
                        "Invalid username or password."
                    )

            except Exception as exc:

                st.error(
                    f"Login failed. Please try again.\n\n{exc}"
                )


# =========================================================
# CREATE ACCOUNT
# =========================================================

with create_tab:

    st.markdown("### Create your account 👤")

    st.info(
        "Create your account once. "
        "Your password is stored securely as a hash "
        "and is never stored as plain text."
    )

    new_username = st.text_input(
        "Username",
        placeholder="Choose a username",
        key="create_username",
    )

    new_password = st.text_input(
        "Password",
        type="password",
        placeholder="Choose a password",
        key="create_password",
    )

    confirm_password = st.text_input(
        "Confirm Password",
        type="password",
        placeholder="Re-enter your password",
        key="confirm_password",
    )

    st.caption(
        "Use a strong password that you do not use elsewhere."
    )

    if st.button(
        "👤 Create Account",
        use_container_width=True,
        type="primary",
    ):

        username_clean = new_username.strip()

        if not username_clean:

            st.error(
                "Please enter a username."
            )

        elif len(username_clean) < 3:

            st.error(
                "Username must contain at least 3 characters."
            )

        elif not new_password:

            st.error(
                "Please enter a password."
            )

        elif len(new_password) < 8:

            st.error(
                "Password must contain at least 8 characters."
            )

        elif new_password != confirm_password:

            st.error(
                "Passwords do not match."
            )

        else:

            try:

                user = create_user(
                    username_clean,
                    new_password,
                )

                if user:

                    st.success(
                        "Account created successfully!"
                    )

                    st.info(
                        "Go to the Login tab and enter your credentials."
                    )

                else:

                    st.error(
                        "Account could not be created."
                    )

            except Exception as exc:

                error_text = str(exc).lower()

                if (
                    "duplicate" in error_text
                    or "unique" in error_text
                    or "already exists" in error_text
                ):

                    st.error(
                        "That username already exists. "
                        "Please choose another username."
                    )

                else:

                    st.error(
                        f"Could not create account.\n\n{exc}"
                    )


st.markdown(
    "</div>",
    unsafe_allow_html=True,
)