"""
query3_rfm_segmentation.py
------------------------------
BUSINESS QUESTION: Which customers are worth targeting for win-back campaigns,
and which aren't worth the effort?

WHAT THIS QUERY DOES:
1. For each customer, calculates:
   - Recency: how many days ago was their LAST order?
   - Frequency: how many total orders have they placed?
   - Monetary: how much have they spent in total?
2. Splits customers into 4 equal-sized groups (quartiles) based on Recency
   and separately based on Monetary value
3. Combines Recency + Monetary + a "repeat buyer" flag into a simple,
   easy-to-explain segment name (e.g. "High-Value Lapsed (At Risk)")

NOTE ON FREQUENCY:
Most customers (97%) only ordered once, so we can't meaningfully split
"frequency" into quartiles -- almost everyone would land in the same bucket.
Instead, we just flag customers as "repeat" (2+ orders) or not.
This is a normal real-world adjustment to textbook RFM.

HOW TO USE:
Run this AFTER build_orders_master.py
    python query3_rfm_segmentation.py
"""

import sqlite3
import pandas as pd

DB_NAME = "olist.db"
conn = sqlite3.connect(DB_NAME)

# Step 1: Get the reference "today" date -- the most recent order in the dataset
max_date = pd.read_sql_query(
    "SELECT MAX(order_purchase_ts) AS d FROM orders_master WHERE order_status NOT IN ('canceled','unavailable')",
    conn
).iloc[0]['d']
print("Reference date for Recency calculation:", max_date)

# Step 2: Calculate raw Recency, Frequency, Monetary per customer
query = f"""
SELECT
    customer_unique_id,
    julianday('{max_date}') - julianday(MAX(order_purchase_ts)) AS recency_days,
    COUNT(DISTINCT order_id) AS frequency,
    SUM(order_revenue) AS monetary
FROM orders_master
WHERE order_status NOT IN ('canceled','unavailable')
GROUP BY customer_unique_id
"""
df = pd.read_sql_query(query, conn)
df = df.dropna(subset=['monetary'])

# Step 3: Split into quartiles
# Recency: LOWER days = BETTER (more recent), so we reverse the labels (4=best/most recent)
df['R_score'] = pd.qcut(df['recency_days'], 4, labels=[4, 3, 2, 1]).astype(int)
# Monetary: HIGHER spend = BETTER, so 4=best/highest spender
df['M_score'] = pd.qcut(df['monetary'], 4, labels=[1, 2, 3, 4]).astype(int)
df['is_repeat'] = df['frequency'] > 1

# Step 4: Assign a plain-English segment name based on the combination
def segment(row):
    if row['is_repeat'] and row['R_score'] >= 3:
        return 'Loyal Active'
    elif row['is_repeat'] and row['R_score'] < 3:
        return 'Loyal Lapsed'
    elif row['M_score'] == 4 and row['R_score'] >= 3:
        return 'High-Value New/Active'
    elif row['M_score'] == 4 and row['R_score'] < 3:
        return 'High-Value Lapsed (At Risk)'
    elif row['R_score'] >= 3:
        return 'Low-Value Active'
    else:
        return 'Low-Value Lapsed'

df['segment'] = df.apply(segment, axis=1)

# Step 5: Summarize each segment
summary = df.groupby('segment').agg(
    num_customers=('customer_unique_id', 'count'),
    avg_monetary=('monetary', 'mean'),
    avg_recency_days=('recency_days', 'mean')
).round(1).sort_values('num_customers', ascending=False)
summary['pct'] = round(100 * summary['num_customers'] / summary['num_customers'].sum(), 2)

print("\nCustomer Segments:")
print(summary.to_string())

# Save full customer-level data (for your dashboard) and the summary
df.to_csv("customer_rfm_segmented.csv", index=False)
summary.to_csv("rfm_segment_summary.csv")
print("\nSaved: customer_rfm_segmented.csv (full detail) and rfm_segment_summary.csv (summary)")

conn.close()