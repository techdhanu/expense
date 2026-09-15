import streamlit as st
from supabase import create_client


@st.cache_resource
def get_supabase_client():
    """
    Create and return one cached Supabase client
    using Streamlit secrets.
    """

    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_secret_key = st.secrets["SUPABASE_SECRET_KEY"]
    except KeyError as exc:
        raise RuntimeError(
            "Missing Supabase configuration in .streamlit/secrets.toml"
        ) from exc

    if not supabase_url or not supabase_secret_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SECRET_KEY must not be empty."
        )

    return create_client(
        supabase_url,
        supabase_secret_key,
    )