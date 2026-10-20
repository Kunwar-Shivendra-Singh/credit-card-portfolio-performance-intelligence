
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

accounts = pd.read_csv(DATA_DIR / "accounts.csv")
monthly = pd.read_csv(DATA_DIR / "monthly_performance.csv")
transactions = pd.read_csv(DATA_DIR / "transactions.csv")

print("\n--- DATA VALIDATION REPORT ---")

# 1. Record counts
print("\nRecord counts")
print(f"Accounts: {len(accounts):,}")
print(f"Monthly records: {len(monthly):,}")
print(f"Purchase records: {len(transactions):,}")

# 2. Duplicate checks
print("\nDuplicate checks")
print("Duplicate account IDs:", accounts["account_id"].duplicated().sum())
print(
    "Duplicate account-month rows:",
    monthly.duplicated(["account_id", "reporting_month"]).sum(),
)

# 3. Missing-value checks
print("\nMissing values")
print("Accounts:\n", accounts.isna().sum())
print("Monthly performance:\n", monthly.isna().sum())
print("Transactions:\n", transactions.isna().sum())

# 4. Business-rule checks
print("\nBusiness-rule checks")
print("Non-positive account credit limits:", (accounts["credit_limit"] <= 0).sum())
print("Negative monthly spending:", (monthly["purchase_spend"] < 0).sum())
print("Negative outstanding balances:", (monthly["outstanding_balance"] < 0).sum())
print(
    "Balances above credit limit:",
    (monthly["outstanding_balance"] > monthly["credit_limit"]).sum(),
)

print("\nValidation report completed.")

