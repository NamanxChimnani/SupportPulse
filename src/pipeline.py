from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "supportpulse.db"

tickets = pd.read_csv(ROOT/"data/tickets.csv", parse_dates=["created_at"])
customers = pd.read_csv(ROOT/"data/customers.csv")

# Data quality gates
assert tickets.ticket_id.is_unique, "Duplicate ticket IDs"
assert tickets.customer_id.isin(customers.customer_id).all(), "Unknown customers"
assert tickets.message_length.gt(0).all(), "Invalid message length"
assert tickets.sla_breach.isin([0,1]).all(), "Invalid target"

conn = sqlite3.connect(DB)
tickets.to_sql("tickets_raw", conn, if_exists="replace", index=False)
customers.to_sql("customers", conn, if_exists="replace", index=False)

# Analytical view
conn.executescript("""
DROP VIEW IF EXISTS ticket_analytics;

CREATE VIEW ticket_analytics AS
SELECT
    t.ticket_id,
    t.customer_id,
    DATE(t.created_at) AS created_date,
    t.product,
    t.channel,
    t.priority,
    t.customer_plan,
    t.previous_tickets_30d,
    t.message_length,
    t.agent_experience_months,
    t.sla_breach,
    c.monthly_spend,
    c.months_active
FROM tickets_raw t
JOIN customers c USING(customer_id);
""")

# Business marts
conn.executescript("""
DROP VIEW IF EXISTS daily_kpis;
CREATE VIEW daily_kpis AS
SELECT
    created_date,
    COUNT(*) tickets,
    ROUND(AVG(sla_breach)*100,2) breach_rate_pct,
    ROUND(AVG(message_length),0) avg_message_length
FROM ticket_analytics
GROUP BY created_date
ORDER BY created_date;

DROP VIEW IF EXISTS product_kpis;
CREATE VIEW product_kpis AS
SELECT
    product,
    COUNT(*) tickets,
    ROUND(AVG(sla_breach)*100,2) breach_rate_pct
FROM ticket_analytics
GROUP BY product
ORDER BY breach_rate_pct DESC;

DROP VIEW IF EXISTS customer_risk;
CREATE VIEW customer_risk AS
SELECT
    customer_id,
    customer_plan,
    monthly_spend,
    COUNT(*) tickets,
    ROUND(AVG(sla_breach)*100,2) breach_rate_pct,
    MAX(previous_tickets_30d) recent_ticket_peak,
    CASE
      WHEN AVG(sla_breach) >= .45 OR COUNT(*) >= 15 THEN 'HIGH'
      WHEN AVG(sla_breach) >= .25 OR COUNT(*) >= 8 THEN 'MEDIUM'
      ELSE 'LOW'
    END AS risk
FROM ticket_analytics
GROUP BY customer_id, customer_plan, monthly_spend;
""")

conn.close()
print(f"Pipeline complete: {DB}")
