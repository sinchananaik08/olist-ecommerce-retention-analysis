"""
load_data.py
-------------
Loads all Olist CSV files into a single SQLite database.

HOW TO USE:
1. Put all your CSV files inside a folder named "data" next to this script.
2. Run this file (in VS Code: right-click -> "Run Python File in Terminal",
   or in the terminal type: python load_data.py)
3. A file called "olist.db" will be created in this same folder.
   That's your database -- open it with the "SQLite Viewer" extension in VS Code,
   or query it from another Python script.
"""

import sqlite3
import pandas as pd
import os

# Folder where your CSV files live
DATA_FOLDER = "data"

# Name of the database file that will be created
DB_NAME = "olist.db"

# Map: table_name -> csv_filename
files = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

# Connect to (or create) the database file
conn = sqlite3.connect(DB_NAME)

for table_name, filename in files.items():
    path = os.path.join(DATA_FOLDER, filename)

    if not os.path.exists(path):
        print(f"SKIPPED: {filename} not found in '{DATA_FOLDER}' folder")
        continue

    # Read the CSV into a pandas DataFrame (basically a table in memory)
    df = pd.read_csv(path, encoding="utf-8-sig")

    # Write that DataFrame into the SQLite database as a table
    # if_exists="replace" means: if the table already exists, overwrite it
    df.to_sql(table_name, conn, if_exists="replace", index=False)

    print(f"Loaded '{table_name}': {len(df)} rows, {len(df.columns)} columns")

conn.close()
print("\nDone! Your database is ready: " + DB_NAME)