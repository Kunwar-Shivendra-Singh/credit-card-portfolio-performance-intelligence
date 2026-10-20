
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load source datasets
accounts = pd.read_csv(DATA_DIR / "accounts.csv")
monthly = pd.read_csv(DATA_DIR / "monthly_performance.csv")

monthly["reporting_month"] = pd.to_datetime(
    monthly["reporting_month"]
)

# Attach product information to every account-month record
data = monthly.merge(
    accounts[["account_id", "product"]],
    on="account_id",
    how="left",
    validate="many_to_one",
)

# Aggregate performance by month and product
monthly_product_kpis = (
    data.groupby(["reporting_month", "product"])
    .agg(
        account_months=("account_id", "size"),
        active_accounts=("active", "sum"),
        total_purchase_spend=("purchase_spend", "sum"),
        total_outstanding_balance=("outstanding_balance", "sum"),
        total_credit_limit=("credit_limit", "sum"),
    )
    .reset_index()
)

# Calculate rates using the correct denominators
monthly_product_kpis["active_rate_pct"] = (
    monthly_product_kpis["active_accounts"]
    / monthly_product_kpis["account_months"]
    * 100
)

monthly_product_kpis["credit_utilization_pct"] = (
    monthly_product_kpis["total_outstanding_balance"]
    / monthly_product_kpis["total_credit_limit"]
    * 100
)

# Sort the output chronologically
monthly_product_kpis = monthly_product_kpis.sort_values(
    ["reporting_month", "product"]
)

# Export results
output_file = OUTPUT_DIR / "monthly_product_kpis.csv"

monthly_product_kpis.to_csv(output_file, index=False)

print("\nMONTHLY PRODUCT PERFORMANCE")
print(monthly_product_kpis.round(2).to_string(index=False))
print(f"\nRows generated: {len(monthly_product_kpis)}")
print(f"Saved to: {output_file}")

