import streamlit as st


def metric_card(
    title: str,
    value: str,
    icon: str = "💰",
    subtitle: str = "",
    card_type: str = "default",
) -> None:
    """
    Display a modern financial metric card.

    card_type:
        default  -> neutral
        positive -> income / positive value
        negative -> expense / negative value
        warning  -> liability / attention
    """

    valid_types = {
        "default": "metric-default",
        "positive": "metric-positive",
        "negative": "metric-negative",
        "warning": "metric-warning",
    }

    css_class = valid_types.get(card_type, "metric-default")

    st.markdown(
        f"""
        <div class="metric-card {css_class}">
            <div class="metric-top">
                <span class="metric-icon">{icon}</span>
                <span class="metric-title">{title}</span>
            </div>

            <div class="metric-value">
                {value}
            </div>

            {f'<div class="metric-subtitle">{subtitle}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(
    title: str,
    subtitle: str = "",
    icon: str = "",
) -> None:
    """
    Display a consistent section heading.
    """

    st.markdown(
        f"""
        <div class="section-header">
            <div class="section-title">
                {icon} {title}
            </div>
            {f'<div class="section-subtitle">{subtitle}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_card(
    title: str,
    content: str,
    icon: str = "ℹ️",
) -> None:
    """
    Display a general information card.
    """

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-card-title">
                <span>{icon}</span>
                <span>{title}</span>
            </div>
            <div class="info-card-content">
                {content}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )