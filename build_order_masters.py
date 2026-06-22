"""
build_orders_master.py
------------------------
Builds a clean "orders_master" table that combines:
- orders (status, dates)
- customers (who, location)
- order_items (aggregated revenue per order)
- order_payments (aggregated payment info per order)
- order_reviews (average review score per order)

WHY WE NEED THIS:
- Dates in the raw "orders" table are stored as text (DD-MM-YYYY), not real dates.
- order_items has MULTIPLE rows per order (one per item) -- if we don't aggregate,
  we'd double-count revenue when joining to other tables.
- order_payments also has multiple rows per order (e.g. split/installment payments) --
  same double-counting risk.

This script fixes both issues and creates ONE clean row per order.

HOW TO USE:
Run this AFTER load_data.py (it needs olist.db to already exist).
    python build_orders_master.py
"""

import sqlite3

DB_NAME = "olist.db"

conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

# Drop the table if it already exists, so we can rebuild it fresh
cur.execute("DROP TABLE IF EXISTS orders_master")

cur.execute("""
CREATE TABLE orders_master AS
WITH item_agg AS (
    -- Combine all items belonging to the same order into ONE row
    SELECT order_id,
           COUNT(*) AS total_items,
           SUM(price) AS total_price,
           SUM(freight_value) AS total_freight,
           SUM(price + freight_value) AS order_revenue
    FROM order_items
    GROUP BY order_id
),
payment_agg AS (
    -- Combine all payment rows (e.g. split payments) into ONE row per order
    SELECT order_id,
           SUM(payment_value) AS total_paid,
           MAX(payment_installments) AS max_installments,
           GROUP_CONCAT(DISTINCT payment_type) AS payment_types
    FROM order_payments
    GROUP BY order_id
),
review_agg AS (
    -- Average review score per order (usually just one review, but just in case)
    SELECT order_id,
           AVG(review_score) AS review_score
    FROM order_reviews
    GROUP BY order_id
)
SELECT
    o.order_id,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    o.order_status,
    -- Convert "02-10-2017 10:56" (DD-MM-YYYY HH:MM) into a real datetime
    -- by rearranging the text into YYYY-MM-DD HH:MM format
    datetime(
        substr(o.order_purchase_timestamp, 7, 4) || '-' ||
        substr(o.order_purchase_timestamp, 4, 2) || '-' ||
        substr(o.order_purchase_timestamp, 1, 2) || ' ' ||
        substr(o.order_purchase_timestamp, 12, 5)
    ) AS order_purchase_ts,
    ia.total_items,
    ia.order_revenue,
    pa.total_paid,
    pa.max_installments,
    pa.payment_types,
    ra.review_score
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN item_agg ia ON o.order_id = ia.order_id
LEFT JOIN payment_agg pa ON o.order_id = pa.order_id
LEFT JOIN review_agg ra ON o.order_id = ra.order_id
""")

conn.commit()

# Quick check: how many rows did we get, and show a sample
cur.execute("SELECT COUNT(*) FROM orders_master")
print("orders_master rows:", cur.fetchone()[0])

cur.execute("SELECT * FROM orders_master LIMIT 3")
cols = [d[0] for d in cur.description]
print(cols)
for row in cur.fetchall():
    print(row)

conn.close()
print("\nDone! 'orders_master' table created inside olist.db")