"""
query2_repeat_customers.py
-----------------------------
BUSINESS QUESTION: What percentage of customers ever buy more than once?

WHAT THIS QUERY DOES:
1. For each unique customer, counts how many orders they've placed in total
2. Labels them "One-time" (exactly 1 order) or "Repeat" (2 or more orders)
3. Counts how many customers fall into each group, and what % of the total that is

HOW TO USE:
Run this AFTER build_orders_master.py
    python query2_repeat_customers.py
"""

import sqlite3
import pandas as pd

DB_NAME = "olist.db"
conn = sqlite3.connect(DB_NAME)

query = """
WITH customer_orders AS (
    -- Step 1: count how many orders each unique person has placed
    SELECT customer_unique_id, COUNT(DISTINCT order_id) AS num_orders
    FROM orders_master
    WHERE order_status NOT IN ('canceled', 'unavailable')
    GROUP BY customer_unique_id
)
-- Step 2: label each customer, then count customers per label
SELECT
    CASE WHEN num_orders = 1 THEN 'One-time' ELSE 'Repeat' END AS customer_type,
    COUNT(*) AS num_customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_customers
FROM customer_orders
GROUP BY customer_type
"""

df = pd.read_sql_query(query, conn)
print(df.to_string(index=False))

df.to_csv("repeat_vs_onetime.csv", index=False)
print("\nSaved to repeat_vs_onetime.csv")

conn.close()