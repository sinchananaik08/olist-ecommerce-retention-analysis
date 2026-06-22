"""
query1_monthly_revenue.py
---------------------------
BUSINESS QUESTION: Is revenue growing, shrinking, or flat month over month?

WHAT THIS QUERY DOES:
1. Groups every order by the month it was purchased (e.g. all of March 2017 together)
2. For each month, counts: how many orders, how many unique customers, total revenue, average order value
3. Excludes canceled/unavailable orders since those never generated real revenue

HOW TO USE:
Run this AFTER build_orders_master.py
    python query1_monthly_revenue.py
"""

import sqlite3
import pandas as pd

DB_NAME = "olist.db"
conn = sqlite3.connect(DB_NAME)

query = """
SELECT
    strftime('%Y-%m', order_purchase_ts) AS order_month,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_unique_id) AS unique_customers,
    ROUND(SUM(order_revenue), 2) AS total_revenue,
    ROUND(AVG(order_revenue), 2) AS avg_order_value
FROM orders_master
WHERE order_status NOT IN ('canceled', 'unavailable')
GROUP BY order_month
ORDER BY order_month
"""

df = pd.read_sql_query(query, conn)
print(df.to_string(index=False))

# Save the result as a CSV -- you'll use this later for your dashboard
df.to_csv("monthly_revenue.csv", index=False)
print("\nSaved to monthly_revenue.csv")

conn.close()