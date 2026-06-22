"""
query4_cohort_retention.py
------------------------------
BUSINESS QUESTION: For customers grouped by the month they FIRST bought
(their "cohort"), what % of them are still buying 1, 2, 3+ months later?

WHAT THIS QUERY DOES:
1. Finds each customer's "cohort month" -- the month of their very first order
2. Finds every month each customer placed ANY order
3. Calculates "month number" -- how many months after their first order was
   each subsequent order (0 = the month they joined, 1 = one month later, etc.)
4. Builds a table: rows = cohort month, columns = months since joining,
   values = % of that cohort still buying

HOW TO USE:
Run this AFTER build_orders_master.py
    python query4_cohort_retention.py
"""

import sqlite3
import pandas as pd

DB_NAME = "olist.db"
conn = sqlite3.connect(DB_NAME)

# Step 1: Get every (customer, order_month) pair, plus each customer's first order month
query = """
WITH customer_orders AS (
    SELECT
        customer_unique_id,
        strftime('%Y-%m', order_purchase_ts) AS order_month
    FROM orders_master
    WHERE order_status NOT IN ('canceled', 'unavailable')
    GROUP BY customer_unique_id, order_month  -- one row per customer per month (dedupes same-month repeat orders)
),
first_order AS (
    SELECT customer_unique_id, MIN(order_month) AS cohort_month
    FROM customer_orders
    GROUP BY customer_unique_id
)
SELECT
    co.customer_unique_id,
    fo.cohort_month,
    co.order_month
FROM customer_orders co
JOIN first_order fo ON co.customer_unique_id = fo.customer_unique_id
"""

df = pd.read_sql_query(query, conn)

# Step 2: Calculate "months since joining" using pandas (easier than pure SQL for this)
df['cohort_month'] = pd.to_datetime(df['cohort_month'])
df['order_month'] = pd.to_datetime(df['order_month'])

# Convert to a single number representing "year*12 + month" so subtracting gives month difference
def month_index(date):
    return date.year * 12 + date.month

df['month_number'] = df['order_month'].apply(month_index) - df['cohort_month'].apply(month_index)

# Step 3: Count how many unique customers are active at each (cohort, month_number)
cohort_counts = df.groupby(['cohort_month', 'month_number'])['customer_unique_id'].nunique().reset_index()
cohort_counts.columns = ['cohort_month', 'month_number', 'num_customers']

# Step 4: Pivot into a table: rows = cohort month, columns = month_number, values = customer count
cohort_pivot = cohort_counts.pivot(index='cohort_month', columns='month_number', values='num_customers')

# Step 5: Convert counts into PERCENTAGES of each cohort's starting size (month_number = 0)
cohort_size = cohort_pivot[0]
retention_pct = cohort_pivot.divide(cohort_size, axis=0) * 100
retention_pct = retention_pct.round(1)

print("Cohort sizes (number of NEW customers acquired each month):")
print(cohort_size.to_string())

print("\nRetention % table (rows=cohort month, columns=months since first purchase):")
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
print(retention_pct.to_string())

# Step 6: Also calculate an OVERALL average retention by month_number, across all cohorts
overall_retention = cohort_counts.groupby('month_number')['num_customers'].sum()
overall_total = cohort_size.sum()
overall_pct = (overall_retention / overall_total * 100).round(2)
print("\nOverall average retention % by month number (across ALL cohorts combined):")
print(overall_pct.to_string())

retention_pct.to_csv("cohort_retention_pct.csv")
cohort_size.to_csv("cohort_sizes.csv")
print("\nSaved: cohort_retention_pct.csv and cohort_sizes.csv")

conn.close()