# Olist E-Commerce Retention Analysis
### Why do 97% of customers never come back — and what should the business do about it?

**Live Dashboard:** [View on Tableau Public](https://public.tableau.com/app/profile/sinchana.naik/viz/Olist_dashboard_17821031298130/OlistE-CommerceWhy97ofCustomersNeverReturn)

**Tools used:** SQL (SQLite), Python (pandas), Tableau
**Dataset:** [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — ~100,000 real, anonymized orders from a Brazilian e-commerce marketplace (Sept 2016 – Sept 2018)

---

## 1. The Business Problem

Olist's revenue grew steadily through 2017. But revenue growth alone doesn't prove a business is healthy — it can just as easily mean the company is constantly paying to acquire new customers while losing the ones it already has.

**This project investigates:** Is Olist's growth being driven by a loyal, returning customer base — or by constant new-customer acquisition? If it's the latter, which customers are most worth winning back, and why are they leaving?

---

## 2. The Dataset

The Olist dataset contains 8 relational tables covering real orders placed on a Brazilian e-commerce marketplace:

| File | Contents |
|---|---|
| `olist_orders_dataset.csv` | Order status and timestamps (purchase, approval, delivery) |
| `olist_customers_dataset.csv` | Customer ID and location |
| `olist_order_items_dataset.csv` | Items, prices, and freight cost per order |
| `olist_order_payments_dataset.csv` | Payment method, installments, amount paid |
| `olist_order_reviews_dataset.csv` | Review scores (1–5 stars) and comments |
| `olist_products_dataset.csv` | Product category and attributes |
| `olist_sellers_dataset.csv` | Seller ID and location |
| `product_category_name_translation.csv` | Portuguese-to-English category translation |

---

## 3. Step-by-Step Process

### Step 1 — Load raw data into a SQL database
All 8 CSVs were loaded into a SQLite database (`olist.db`) using Python (`pandas` + `sqlite3`), creating one table per file. *(Script: `load_data.py`)*

### Step 2 — Clean and consolidate into a master table
Two real data problems had to be fixed before any analysis could be trusted:
- **Broken date format:** Timestamps were stored as text in `DD-MM-YYYY HH:MM` format, which SQL couldn't read as real dates. Fixed by rearranging the text into proper datetime format.
- **Double-counting risk:** Both `order_items` (multiple rows per order) and `order_payments` (multiple rows per order for split/installment payments) would inflate revenue totals if joined naively. Fixed by aggregating each to one row per order *before* joining.

This produced `orders_master` — one clean row per order, with correct revenue, payment info, and review scores attached. *(Script: `build_orders_master.py`)*

### Step 3 — Monthly Revenue Trend Analysis
**Question:** Is revenue growing, shrinking, or flat over time?
**Method:** Grouped orders by month, summed revenue, excluded canceled/unavailable orders and incomplete edge months (the dataset's first/last months had only 1–2 orders).
**Finding:** Revenue grew ~9x from Jan 2017 ($137K) to a Black Friday peak in Nov 2017 (~$1.17M), then plateaued through 2018 at $1M–$1.2M/month with no further growth.
*(Script: `query1_monthly_revenue.py`)*

### Step 4 — Repeat vs. One-Time Customer Analysis
**Question:** What percentage of customers ever buy more than once?
**Method:** Counted total orders per unique customer; labeled each as "One-time" (1 order) or "Repeat" (2+).
**Finding:** **96.96% of customers never make a second purchase.** Only 3.04% are repeat buyers.
*(Script: `query2_repeat_customers.py`)*

### Step 5 — Validity Check on the Repeat Rate
**Question:** Could the 97% figure be misleadingly high just because recent customers haven't had time to return yet?
**Method:** Re-ran the repeat-rate calculation using only customers whose first order was at least 6 months before the dataset's last recorded date — giving every included customer a fair chance to return.
**Finding:** The repeat rate only rose to 4.01% — confirming the low retention is a real pattern, not a timing artifact.
*(Script: `repeat_rate_caveat_test.py`)*

### Step 6 — Customer Segmentation (Adapted RFM)
**Question:** Among the customers who could be targeted for retention, which are actually worth the effort?
**Method:** Calculated Recency, Frequency, and Monetary value per customer. Since 97% of customers had a frequency of exactly 1, a standard 5x5x5 RFM grid wasn't meaningful — instead, Recency and Monetary were split into quartiles, and Frequency was used as a simple "repeat buyer" flag. Combined into 6 plain-English segments.
**Finding:** "High-Value Lapsed (At Risk)" customers (11.5% of the base, ~$394 avg. spend) are nearly identical in size to currently active high-value customers (11.6%, ~$391 avg. spend) — the business is losing close to half its best customers to inactivity.
*(Script: `rfm_segmentation.py`)*

### Step 7 — Cohort Retention Analysis
**Question:** When exactly do customers stop buying — gradually, or all at once?
**Method:** Grouped customers by the month of their first order ("cohort"), then tracked what % of each cohort was still purchasing in each subsequent month.
**Finding:** Every cohort drops from 100% to under 1% retention within a single month, and stays near-zero for up to 20 months afterward. This is a cliff, not a gradual decline — suggesting no active mechanism exists to bring customers back.
*(Script: `cohort_retention.py`)*

### Step 8 — Does Review Score Predict Churn?
**Question:** Are unhappy customers (low review scores) the ones who don't return?
**Method:** Compared the repeat-purchase rate of customers grouped by the star rating they gave their first order.
**Finding:** Repeat rate stayed flat (2.8%–3.2%) regardless of whether the first review was 1 star or 5 stars. This rules out poor product/service experience as the main driver of churn.
*(Script: `review_score_vs_churn.py`)*

### Step 9 — Dashboard Build
All five findings were visualized in Tableau as one interactive dashboard:
1. Monthly Revenue Trend (line chart)
2. Repeat vs. One-Time Customers (bar chart)
3. Customer Segments (bar chart)
4. Repeat Rate vs. Review Score (bar chart)
5. Cohort Retention (heatmap)

Each chart title states the *insight*, not just the metric — e.g. "Customers Drop Off Within One Month and Never Return" instead of "Cohort Retention %."

---

## 4. Final Recommendation

> Olist's growth model currently depends on continuous new-customer acquisition rather than retention — a fragile position if acquisition costs rise. Since churn is not explained by poor product experience, the highest-leverage fix is **building active re-engagement infrastructure** (post-purchase email campaigns, loyalty incentives, personalized win-back offers) — starting with the "High-Value Lapsed" segment, which represents the single largest pool of recoverable revenue, roughly equal in size to the currently active high-value customer base.

---

## 5. Repository Structure
```
olist-project/
├── data/                              # Raw Kaggle CSVs
├── outputs/                           # Generated analysis CSVs
├── load_data.py                       # Step 1: Load raw CSVs into SQLite
├── build_orders_master.py             # Step 2: Build cleaned master table
├── query1_monthly_revenue.py          # Step 3: Revenue trend
├── query2_repeat_customers.py         # Step 4: Repeat vs one-time
├── repeat_rate_caveat_test.py         # Step 5: Validity check
├── rfm_segmentation.py                # Step 6: Customer segmentation
├── cohort_retention.py                # Step 7: Cohort retention
├── review_score_vs_churn.py           # Step 8: Review score vs churn
├── olist.db                           # SQLite database
└── README.md
```

## 6. How to Reproduce This Project
1. Download the dataset from [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and place the CSVs in `data/`
2. Install dependencies: `pip install pandas`
3. Run the scripts in order:
```
python load_data.py
python build_orders_master.py
python query1_monthly_revenue.py
python query2_repeat_customers.py
python repeat_rate_caveat_test.py
python rfm_segmentation.py
python cohort_retention.py
python review_score_vs_churn.py
```
4. Open the generated CSVs in the `outputs/` folder with Tableau to rebuild the dashboard, or view the [live dashboard](https://public.tableau.com/app/profile/sinchana.naik/viz/Olist_dashboard_17821031298130/OlistE-CommerceWhy97ofCustomersNeverReturn) directly.

---

*Analysis by Sinchana Naik | Built as an end-to-end SQL + Python + Tableau portfolio project*
