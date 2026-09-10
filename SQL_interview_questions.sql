-- 1. Top products by SLA-breach rate
SELECT product,
       COUNT(*) AS tickets,
       ROUND(AVG(sla_breach)*100, 2) AS breach_rate_pct
FROM ticket_analytics
GROUP BY product
ORDER BY breach_rate_pct DESC;

-- 2. Customers generating the most tickets
SELECT customer_id, COUNT(*) AS ticket_count
FROM ticket_analytics
GROUP BY customer_id
ORDER BY ticket_count DESC
LIMIT 20;

-- 3. Breach rate by support channel
SELECT channel,
       COUNT(*) tickets,
       ROUND(AVG(sla_breach)*100,2) breach_rate_pct
FROM ticket_analytics
GROUP BY channel
ORDER BY breach_rate_pct DESC;

-- 4. High-value customers with elevated breach rates
SELECT customer_id, monthly_spend,
       COUNT(*) tickets,
       ROUND(AVG(sla_breach)*100,2) breach_rate_pct
FROM ticket_analytics
GROUP BY customer_id, monthly_spend
HAVING monthly_spend > 100
   AND AVG(sla_breach) > .30
ORDER BY monthly_spend DESC;

-- 5. Daily trend
SELECT created_date, COUNT(*) tickets,
       ROUND(AVG(sla_breach)*100,2) breach_rate_pct
FROM ticket_analytics
GROUP BY created_date
ORDER BY created_date;
