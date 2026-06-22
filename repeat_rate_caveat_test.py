"""
query2b_repeat_rate_caveat_test.py
------------------------------------
BUSINESS QUESTION: Is the 97% one-time-buyer rate real, or partly caused by
recent customers simply not having had time to make a second purchase yet?

WHAT THIS QUERY DOES:
1. Finds the very last order date in the whole dataset (our "today")
2. For each customer, finds their FIRST order date
3. Keeps only customers whose first order was at least 6 months before
   that last date -- meaning they've had a fair chance to return if they wanted to
4. Recalculates the repeat vs one-time split on JUST this filtered group

HOW TO USE:
Run this AFTER build_orders_master.py
    python query2b_repeat_rate_caveat_test.py
"""

import sqlite3
import pandas as pd

DB_NAME = "olist.db"
conn = sqlite3.connect(DB_NAME)

query = """
WITH last_date AS (
    -- Step 1: find the most recent order date in the whole dataset
    SELECT MAX(order_purchase_ts) AS max_date
    FROM orders_master
    WHERE order_status NOT IN ('canceled', 'unavailable')
),
customer_first_order AS (
    -- Step 2: find each customer's FIRST order date and total order count
    SELECT
        customer_unique_id,
        MIN(order_purchase_ts) AS first_order_date,
        COUNT(DISTINCT order_id) AS num_orders
    FROM orders_master
    WHERE order_status NOT IN ('canceled', 'unavailable')
    GROUP BY customer_unique_id
),
eligible_customers AS (
    -- Step 3: keep only customers whose FIRST order was at least 6 months
    -- before the dataset's last date (so they had a fair chance to return)
    SELECT cfo.*
    FROM customer_first_order cfo, last_date ld
    WHERE julianday(ld.max_date) - julianday(cfo.first_order_date) >= 180
)
-- Step 4: recalculate repeat vs one-time, but only on the "eligible" group
SELECT
    CASE WHEN num_orders = 1 THEN 'One-time' ELSE 'Repeat' END AS customer_type,
    COUNT(*) AS num_customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_customers
FROM eligible_customers
GROUP BY customer_type
"""

df = pd.read_sql_query(query, conn)
print("Repeat rate among customers who had AT LEAST 6 months to return:")
print(df.to_string(index=False))

conn.close()