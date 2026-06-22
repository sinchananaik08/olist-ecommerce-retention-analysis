"""
query5_review_score_vs_churn.py
-----------------------------------
BUSINESS QUESTION: Does a customer's experience (review score) on their
FIRST order predict whether they come back for a second purchase?

WHAT THIS QUERY DOES:
1. Finds each customer's FIRST order, and the review score they gave it
2. Flags whether that customer ever became a repeat buyer (2+ orders)
3. Groups customers by their first-order review score (1 to 5 stars)
4. For each star rating, calculates what % of customers with that rating
   went on to buy again

WHY THIS MATTERS:
If low review scores strongly predict churn, that points to a PRODUCT/SERVICE
QUALITY problem. If review score barely matters, the churn problem is more
likely about marketing/re-engagement (people just never get reminded to come back),
not about a bad experience.

HOW TO USE:
Run this AFTER build_orders_master.py
    python query5_review_score_vs_churn.py
"""

import sqlite3
import pandas as pd

DB_NAME = "olist.db"
conn = sqlite3.connect(DB_NAME)

query = """
WITH customer_orders AS (
    SELECT
        customer_unique_id,
        order_purchase_ts,
        review_score,
        order_id,
        ROW_NUMBER() OVER (
            PARTITION BY customer_unique_id
            ORDER BY order_purchase_ts
        ) AS order_sequence
    FROM orders_master
    WHERE order_status NOT IN ('canceled', 'unavailable')
),
first_orders AS (
    -- Keep only each customer's FIRST order (order_sequence = 1)
    SELECT customer_unique_id, review_score AS first_review_score
    FROM customer_orders
    WHERE order_sequence = 1
),
customer_total_orders AS (
    SELECT customer_unique_id, COUNT(DISTINCT order_id) AS total_orders
    FROM customer_orders
    GROUP BY customer_unique_id
)
SELECT
    fo.customer_unique_id,
    fo.first_review_score,
    cto.total_orders,
    CASE WHEN cto.total_orders > 1 THEN 1 ELSE 0 END AS is_repeat
FROM first_orders fo
JOIN customer_total_orders cto ON fo.customer_unique_id = cto.customer_unique_id
WHERE fo.first_review_score IS NOT NULL
"""

df = pd.read_sql_query(query, conn)

# Round review scores to nearest whole star (most are already whole numbers)
df['first_review_score'] = df['first_review_score'].round().astype(int)

# Group by star rating: how many customers, and what % became repeat buyers
summary = df.groupby('first_review_score').agg(
    num_customers=('customer_unique_id', 'count'),
    repeat_customers=('is_repeat', 'sum')
)
summary['repeat_rate_pct'] = round(100 * summary['repeat_customers'] / summary['num_customers'], 2)

print("Repeat purchase rate by FIRST ORDER review score (1-5 stars):")
print(summary.to_string())

# Also compare: average review score of repeat buyers vs one-time buyers
avg_by_group = df.groupby('is_repeat')['first_review_score'].mean().round(2)
print("\nAverage first-order review score by customer type (0=One-time, 1=Repeat):")
print(avg_by_group.to_string())

summary.to_csv("review_score_vs_repeat.csv")
print("\nSaved: review_score_vs_repeat.csv")

conn.close()