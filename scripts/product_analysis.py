
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

accounts = pd.read_csv(DATA_DIR / "accounts.csv")
monthly = pd.read_csv(DATA_DIR / "monthly_performance.csv")

# Attach each account's product to its monthly records
data = monthly.merge(
    accounts[["account_id", "product"]],
    on="account_id",
    how="left",
    validate="many_to_one",
)

# Summarise performance by product
product_kpis = (
    data.groupby("product")
    .agg(
        account_months=("account_id", "size"),
        active_account_months=("active", "sum"),
        total_purchase_spend=("purchase_spend", "sum"),
        total_outstanding_balance=("outstanding_balance", "sum"),
        total_credit_limit=("credit_limit", "sum"),
    )
    .reset_index()
)

product_kpis["active_rate_pct"] = (
    product_kpis["active_account_months"]
    / product_kpis["account_months"]
    * 100
)

product_kpis["credit_utilization_pct"] = (
    product_kpis["total_outstanding_balance"]
    / product_kpis["total_credit_limit"]
    * 100
)

product_kpis["spend_per_active_account_month"] = (
    product_kpis["total_purchase_spend"]
    / product_kpis["active_account_months"]
)

product_kpis = product_kpis.sort_values(
    "total_purchase_spend",
    ascending=False,
)

product_kpis.to_csv(
    OUTPUT_DIR / "product_kpis.csv",
    index=False,
)

print("\nPRODUCT PERFORMANCE SUMMARY")
print(product_kpis.round(2).to_string(index=False))
print(f"\nSaved to: {OUTPUT_DIR / 'product_kpis.csv'}")

