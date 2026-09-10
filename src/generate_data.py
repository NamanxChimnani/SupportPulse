import numpy as np
import pandas as pd
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data"
OUT.mkdir(exist_ok=True)

rng = np.random.default_rng(42)

N_TICKETS = 15000
N_CUSTOMERS = 1800

products = [
    "Payments API",
    "Analytics",
    "Authentication",
    "Messaging",
    "Storage"
]

channels = ["Email", "Chat", "Web", "Phone"]
priorities = ["Low", "Medium", "High", "Urgent"]
plans = ["Free", "Starter", "Business", "Enterprise"]

# -----------------------------
# CUSTOMERS
# -----------------------------

customer_ids = np.array(
    [f"C{i:05d}" for i in range(1, N_CUSTOMERS + 1)]
)

customer_plans = rng.choice(
    plans,
    N_CUSTOMERS,
    p=[0.30, 0.40, 0.23, 0.07]
)

customers = pd.DataFrame({
    "customer_id": customer_ids,
    "plan": customer_plans,
    "monthly_spend": np.round(
        rng.lognormal(3.8, 0.65, N_CUSTOMERS),
        2
    ),
    "months_active": rng.integers(
        1,
        48,
        N_CUSTOMERS
    )
})

# -----------------------------
# TICKETS
# -----------------------------

ticket_customer = rng.choice(
    customer_ids,
    N_TICKETS
)

plan_lookup = dict(
    zip(customer_ids, customer_plans)
)

tickets = pd.DataFrame({
    "ticket_id": [
        f"T{i:07d}"
        for i in range(1, N_TICKETS + 1)
    ],

    "customer_id": ticket_customer,

    "created_at":
        pd.Timestamp("2026-01-01")
        + pd.to_timedelta(
            rng.integers(0, 180 * 24, N_TICKETS),
            unit="h"
        ),

    "product": rng.choice(
        products,
        N_TICKETS
    ),

    "channel": rng.choice(
        channels,
        N_TICKETS,
        p=[0.30, 0.35, 0.25, 0.10]
    ),

    "priority": rng.choice(
        priorities,
        N_TICKETS,
        p=[0.30, 0.50, 0.17, 0.03]
    ),

    "previous_tickets_30d":
        rng.poisson(1.2, N_TICKETS),

    "message_length":
        rng.integers(30, 900, N_TICKETS),

    "agent_experience_months":
        rng.integers(3, 72, N_TICKETS)
})

tickets["customer_plan"] = (
    tickets["customer_id"]
    .map(plan_lookup)
)

# -----------------------------
# REALISTIC SLA TARGET
# -----------------------------

priority_effect = tickets["priority"].map({
    "Low": 0.00,
    "Medium": 0.35,
    "High": 1.05,
    "Urgent": 1.90
})

product_effect = tickets["product"].map({
    "Payments API": 0.45,
    "Analytics": 0.10,
    "Authentication": 0.25,
    "Messaging": -0.10,
    "Storage": -0.20
})

channel_effect = tickets["channel"].map({
    "Email": 0.10,
    "Chat": -0.10,
    "Web": 0.00,
    "Phone": 0.25
})

plan_effect = tickets["customer_plan"].map({
    "Free": 0.15,
    "Starter": 0.05,
    "Business": -0.05,
    "Enterprise": -0.15
})

risk_score = (
    -2.65
    + priority_effect
    + product_effect
    + channel_effect
    + plan_effect
    + 0.18 * tickets["previous_tickets_30d"]
    + 0.00035 * tickets["message_length"]
    - 0.012 * tickets["agent_experience_months"]
)

probability = 1 / (
    1 + np.exp(-risk_score)
)

tickets["sla_breach"] = rng.binomial(
    1,
    np.clip(probability, 0.01, 0.70)
)

# -----------------------------
# SAVE
# -----------------------------

customers.to_csv(
    OUT / "customers.csv",
    index=False
)

tickets.to_csv(
    OUT / "tickets.csv",
    index=False
)

print(
    f"Created {len(tickets):,} tickets "
    f"and {len(customers):,} customers."
)

print(
    f"SLA breach rate: "
    f"{tickets['sla_breach'].mean() * 100:.1f}%"
)