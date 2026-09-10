from pathlib import Path
import json
import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# CONFIG
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

st.set_page_config(
    page_title="SupportPulse",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>

.main {
    padding-top: 1rem;
}

.block-container {
    max-width: 1500px;
    padding-top: 2rem;
}

[data-testid="stMetric"] {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 18px;
    border-radius: 12px;
}

[data-testid="stMetricValue"] {
    font-size: 2rem;
}

.risk-card {
    padding: 18px;
    border-radius: 12px;
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.08);
}

.small-text {
    color: #9ca3af;
    font-size: 0.85rem;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD DATA
# ============================================================

db = ROOT / "supportpulse.db"
scored_file = ROOT / "data" / "scored_tickets.csv"
metrics_file = ROOT / "metrics.json"
comparison_file = ROOT / "model_comparison.csv"


if not db.exists() or not scored_file.exists():

    st.error(
        "Required project files are missing. "
        "Run generate_data.py → pipeline.py → train_model.py."
    )

    st.stop()


conn = sqlite3.connect(db)

daily = pd.read_sql(
    "SELECT * FROM daily_kpis",
    conn
)

products = pd.read_sql(
    "SELECT * FROM product_kpis",
    conn
)

customers = pd.read_sql(
    "SELECT * FROM customer_risk",
    conn
)

conn.close()

tickets = pd.read_csv(scored_file)

metrics = {}

if metrics_file.exists():
    metrics = json.loads(
        metrics_file.read_text()
    )


# ============================================================
# NORMALIZE DATA
# ============================================================

tickets["created_date"] = pd.to_datetime(
    tickets["created_date"],
    errors="coerce"
)

daily["created_date"] = pd.to_datetime(
    daily["created_date"],
    errors="coerce"
)


# ============================================================
# HEADER
# ============================================================

st.title("🚦 SupportPulse")

st.markdown(
    "### AI-powered support operations intelligence"
)

st.caption(
    "Predict SLA-breach risk • prioritize support workload • "
    "identify customer risk • support operational decisions"
)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🎛️ Filters")

product_options = ["All"] + sorted(
    tickets["product"].dropna().unique().tolist()
)

priority_options = ["All"] + sorted(
    tickets["priority"].dropna().unique().tolist()
)

plan_options = ["All"] + sorted(
    tickets["customer_plan"].dropna().unique().tolist()
)

channel_options = ["All"] + sorted(
    tickets["channel"].dropna().unique().tolist()
)

selected_product = st.sidebar.selectbox(
    "Product",
    product_options
)

selected_priority = st.sidebar.selectbox(
    "Priority",
    priority_options
)

selected_plan = st.sidebar.selectbox(
    "Customer plan",
    plan_options
)

selected_channel = st.sidebar.selectbox(
    "Channel",
    channel_options
)


filtered = tickets.copy()

if selected_product != "All":
    filtered = filtered[
        filtered["product"] == selected_product
    ]

if selected_priority != "All":
    filtered = filtered[
        filtered["priority"] == selected_priority
    ]

if selected_plan != "All":
    filtered = filtered[
        filtered["customer_plan"] == selected_plan
    ]

if selected_channel != "All":
    filtered = filtered[
        filtered["channel"] == selected_channel
    ]


# ============================================================
# KPI CALCULATIONS
# ============================================================

ticket_count = len(filtered)

if ticket_count > 0:
    breach_rate = (
        filtered["sla_breach"].mean() * 100
    )
else:
    breach_rate = 0


high_risk_customers = (
    filtered[
        filtered["breach_probability"] >= 0.75
    ]["customer_id"]
    .nunique()
)


escalations = (
    filtered["recommended_action"] == "ESCALATE"
).sum()


prioritized = (
    filtered["recommended_action"] == "PRIORITIZE"
).sum()


# ============================================================
# KPI ROW
# ============================================================

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Tickets",
    f"{ticket_count:,}"
)

c2.metric(
    "SLA breach rate",
    f"{breach_rate:.1f}%"
)

c3.metric(
    "High-risk customers",
    f"{high_risk_customers:,}"
)

c4.metric(
    "Escalations",
    f"{escalations:,}"
)

c5.metric(
    "Prioritized",
    f"{prioritized:,}"
)


st.divider()


# ============================================================
# SLA TREND
# ============================================================

st.subheader("📈 SLA performance")

if len(filtered) > 0:

    trend = (
        filtered
        .groupby("created_date")
        .agg(
            tickets=("ticket_id", "count"),
            breach_rate=("sla_breach", "mean")
        )
        .reset_index()
    )

    trend["breach_rate"] *= 100

    fig = px.line(
        trend,
        x="created_date",
        y="breach_rate",
        markers=True,
        labels={
            "created_date": "Date",
            "breach_rate": "SLA breach rate (%)"
        }
    )

    fig.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=20, b=10),
        hovermode="x unified"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    st.info("No tickets match the selected filters.")


# ============================================================
# PRODUCT + PRIORITY
# ============================================================

left, right = st.columns(2)


with left:

    st.subheader("🔥 Breach concentration")

    product_filtered = (
        filtered
        .groupby("product")
        .agg(
            tickets=("ticket_id", "count"),
            breach_rate=("sla_breach", "mean")
        )
        .reset_index()
    )

    product_filtered["breach_rate"] *= 100

    fig = px.bar(
        product_filtered.sort_values(
            "breach_rate",
            ascending=False
        ),
        x="product",
        y="breach_rate",
        text_auto=".1f",
        labels={
            "breach_rate": "Breach rate (%)",
            "product": "Product"
        }
    )

    fig.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=20, b=10)
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with right:

    st.subheader("⚡ Risk by priority")

    priority_df = (
        filtered
        .groupby("priority")
        .agg(
            tickets=("ticket_id", "count"),
            avg_risk=("breach_probability", "mean")
        )
        .reset_index()
    )

    priority_df["avg_risk"] *= 100

    fig = px.bar(
        priority_df,
        x="priority",
        y="avg_risk",
        text_auto=".1f",
        labels={
            "avg_risk": "Average predicted risk (%)",
            "priority": "Priority"
        }
    )

    fig.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=20, b=10)
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# ACTION DISTRIBUTION
# ============================================================

st.subheader("🎯 Operational workload")

action_counts = (
    filtered["recommended_action"]
    .value_counts()
    .rename_axis("action")
    .reset_index(name="tickets")
)

fig = px.bar(
    action_counts,
    x="action",
    y="tickets",
    text_auto=True,
    labels={
        "action": "Recommended action",
        "tickets": "Tickets"
    }
)

fig.update_layout(
    height=320,
    margin=dict(l=10, r=10, t=20, b=10)
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# PRIORITY QUEUE
# ============================================================

st.subheader("🚨 Priority queue")

st.caption(
    "Tickets ranked by predicted SLA-breach probability "
    "and business priority."
)


queue = (
    filtered
    .sort_values(
        "priority_score",
        ascending=False
    )
    .head(25)
    .copy()
)


if len(queue) > 0:

    queue["breach_probability"] = (
        queue["breach_probability"] * 100
    ).round(1)

    queue["priority_score"] = (
        queue["priority_score"]
        .round(1)
    )

    st.dataframe(
        queue[
            [
                "ticket_id",
                "customer_id",
                "product",
                "priority",
                "customer_plan",
                "breach_probability",
                "priority_score",
                "recommended_action",
                "risk_reasons"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("No tickets match the selected filters.")


# ============================================================
# TICKET INVESTIGATION
# ============================================================

st.divider()

st.subheader("🔎 Investigate a ticket")

if len(filtered) > 0:

    ticket_options = filtered[
        "ticket_id"
    ].tolist()

    selected_ticket = st.selectbox(
        "Select ticket",
        ticket_options
    )

    ticket = filtered[
        filtered["ticket_id"] == selected_ticket
    ].iloc[0]


    a, b, c = st.columns(3)

    with a:
        st.metric(
            "SLA breach probability",
            f"{ticket['breach_probability'] * 100:.1f}%"
        )

    with b:
        st.metric(
            "Priority score",
            f"{ticket['priority_score']:.1f}"
        )

    with c:
        st.metric(
            "Recommended action",
            ticket["recommended_action"]
        )


    st.markdown("#### 🧠 Why is this ticket risky?")

    st.info(
        ticket["risk_reasons"]
    )


    details = pd.DataFrame({
        "Attribute": [
            "Product",
            "Channel",
            "Priority",
            "Customer plan",
            "Previous tickets (30d)",
            "Message length",
            "Agent experience",
            "Monthly spend",
            "Months active"
        ],

        "Value": [
            ticket["product"],
            ticket["channel"],
            ticket["priority"],
            ticket["customer_plan"],
            ticket["previous_tickets_30d"],
            ticket["message_length"],
            ticket["agent_experience_months"],
            f"${ticket['monthly_spend']:,.2f}",
            ticket["months_active"]
        ]
    })

    st.dataframe(
        details,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# CUSTOMER 360
# ============================================================

st.divider()

st.subheader("👤 Customer 360")

if len(filtered) > 0:

    customer_options = sorted(
        filtered["customer_id"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_customer = st.selectbox(
        "Select customer",
        customer_options
    )

    customer_tickets = filtered[
        filtered["customer_id"] == selected_customer
    ].copy()


    total_tickets = len(customer_tickets)

    customer_breach_rate = (
        customer_tickets["sla_breach"].mean() * 100
    )

    avg_risk = (
        customer_tickets["breach_probability"].mean() * 100
    )

    spend = (
        customer_tickets["monthly_spend"].iloc[0]
    )

    plan = (
        customer_tickets["customer_plan"].iloc[0]
    )


    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Plan",
        plan
    )

    c2.metric(
        "Tickets",
        total_tickets
    )

    c3.metric(
        "Breach rate",
        f"{customer_breach_rate:.1f}%"
    )

    c4.metric(
        "Average risk",
        f"{avg_risk:.1f}%"
    )


    st.markdown(
        f"**Monthly spend:** ${spend:,.2f}"
    )

    st.markdown("##### Recent tickets")

    st.dataframe(
        customer_tickets.sort_values(
            "created_date",
            ascending=False
        )[
            [
                "ticket_id",
                "created_date",
                "product",
                "priority",
                "breach_probability",
                "recommended_action"
            ]
        ].head(15),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# MODEL PERFORMANCE
# ============================================================

st.divider()

st.subheader("🤖 Model performance")

if metrics:

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "ROC-AUC",
        f"{metrics.get('roc_auc', 0):.3f}"
    )

    m2.metric(
        "Precision",
        f"{metrics.get('precision', 0):.3f}"
    )

    m3.metric(
        "Recall",
        f"{metrics.get('recall', 0):.3f}"
    )

    m4.metric(
        "F1",
        f"{metrics.get('f1', 0):.3f}"
    )


    st.caption(
        f"Selected model: "
        f"{metrics.get('selected_model', 'Unknown')} "
        "• 80/20 stratified train/test split"
    )


# ============================================================
# MODEL COMPARISON
# ============================================================

if comparison_file.exists():

    st.subheader("📊 Model comparison")

    comparison = pd.read_csv(
        comparison_file
    )

    st.dataframe(
        comparison.style.format({
            "roc_auc": "{:.3f}",
            "precision": "{:.3f}",
            "recall": "{:.3f}",
            "f1": "{:.3f}"
        }),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# BUSINESS INSIGHTS
# ============================================================

st.divider()

st.subheader("💡 Automated business insights")

if len(filtered) > 0:

    worst_product = (
        filtered
        .groupby("product")["sla_breach"]
        .mean()
        .idxmax()
    )

    worst_product_rate = (
        filtered
        .groupby("product")["sla_breach"]
        .mean()
        .max()
        * 100
    )

    urgent_count = (
        filtered["priority"] == "Urgent"
    ).sum()

    high_risk_pct = (
        (
            filtered["breach_probability"] >= 0.75
        ).mean()
        * 100
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.markdown(
            f"""
            **Highest-risk product**

            `{worst_product}`

            {worst_product_rate:.1f}% observed breach rate
            """
        )


    with col2:

        st.markdown(
            f"""
            **High-risk workload**

            `{high_risk_pct:.1f}%`

            of filtered tickets have predicted risk ≥ 75%.
            """
        )


    with col3:

        st.markdown(
            f"""
            **Urgent workload**

            `{urgent_count:,}`

            urgent tickets in the current view.
            """
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "SupportPulse • Data Engineering + Machine Learning "
    "portfolio project • Predictions are decision-support signals, "
    "not automatic operational decisions."
)