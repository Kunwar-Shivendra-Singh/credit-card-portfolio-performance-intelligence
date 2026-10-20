
from pathlib import Path
import sqlite3

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DB_PATH = PROJECT_ROOT / "portfolio.db"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Read source data.
accounts = pd.read_csv(DATA_DIR / "accounts.csv")
monthly = pd.read_csv(
    DATA_DIR / "monthly_performance.csv",
    parse_dates=["reporting_month"],
)
transactions = pd.read_csv(
    DATA_DIR / "transactions.csv",
    parse_dates=["transaction_month"],
)

# Store dates in ISO format so SQLite can sort them consistently.
monthly["reporting_month"] = (
    monthly["reporting_month"].dt.strftime("%Y-%m-%d")
)
transactions["transaction_month"] = (
    transactions["transaction_month"].dt.strftime("%Y-%m-%d")
)

# Create or connect to the database.
with sqlite3.connect(DB_PATH) as connection:
    accounts.to_sql(
        "accounts",
        connection,
        if_exists="replace",
        index=False,
    )

    monthly.to_sql(
        "monthly_performance",
        connection,
        if_exists="replace",
        index=False,
    )

    transactions.to_sql(
        "transactions",
        connection,
        if_exists="replace",
        index=False,
    )

    # Add indexes to support common joins and time-based queries.
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_monthly_account "
        "ON monthly_performance(account_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_monthly_month "
        "ON monthly_performance(reporting_month)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_account "
        "ON transactions(account_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_month "
        "ON transactions(transaction_month)"
    )

    # Verify the loaded row counts.
    tables = [
        "accounts",
        "monthly_performance",
        "transactions",
    ]

    print("\nDATABASE LOAD SUMMARY")
    print("=" * 45)

    for table in tables:
        row_count = connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        print(f"{table}: {row_count:,} rows")

    print("\nDATABASE TABLES")
    table_info = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()

    for (table_name,) in table_info:
        print(f"- {table_name}")

print(f"\nDatabase saved to: {DB_PATH}")

