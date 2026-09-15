import pandas as pd
import plotly.express as px
import streamlit as st


def show_expense_by_category(
    data: pd.DataFrame,
    title: str = "Expenses by Category",
) -> None:
    """
    Display an expense distribution chart.
    """

    if data is None or data.empty:
        st.info("No expense data available for this period.")
        return

    required_columns = {"category", "amount"}

    if not required_columns.issubset(data.columns):
        st.warning("Unable to display the expense chart.")
        return

    chart_data = (
        data.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )

    if chart_data.empty:
        st.info("No expense data available for this period.")
        return

    fig = px.pie(
        chart_data,
        names="category",
        values="amount",
        hole=0.55,
        title=title,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>₹%{value:,.2f}<extra></extra>",
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )


def show_income_vs_expense(
    data: pd.DataFrame,
    title: str = "Income vs Expenses",
) -> None:
    """
    Display an income-versus-expense comparison chart.
    """

    if data is None or data.empty:
        st.info("No financial data available for this period.")
        return

    required_columns = {"date", "income", "expense"}

    if not required_columns.issubset(data.columns):
        st.warning("Unable to display the income/expense chart.")
        return

    chart_data = data.copy()

    chart_data["date"] = pd.to_datetime(chart_data["date"])

    chart_data = chart_data.sort_values("date")

    fig = px.bar(
        chart_data,
        x="date",
        y=["income", "expense"],
        barmode="group",
        title=title,
        labels={
            "date": "",
            "value": "Amount (₹)",
            "variable": "",
        },
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        xaxis=dict(
            showgrid=False,
        ),
        yaxis=dict(
            showgrid=True,
            tickprefix="₹",
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )


def show_balance_trend(
    data: pd.DataFrame,
    title: str = "Balance Trend",
) -> None:
    """
    Display the account balance trend.
    """

    if data is None or data.empty:
        st.info("No balance data available for this period.")
        return

    required_columns = {"date", "balance"}

    if not required_columns.issubset(data.columns):
        st.warning("Unable to display the balance chart.")
        return

    chart_data = data.copy()

    chart_data["date"] = pd.to_datetime(chart_data["date"])

    chart_data = chart_data.sort_values("date")

    fig = px.line(
        chart_data,
        x="date",
        y="balance",
        title=title,
        markers=True,
        labels={
            "date": "",
            "balance": "Balance (₹)",
        },
    )

    fig.update_traces(
        hovertemplate="₹%{y:,.2f}<extra></extra>",
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(
            showgrid=False,
        ),
        yaxis=dict(
            showgrid=True,
            tickprefix="₹",
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )