
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

monthly = pd.read_csv(DATA_DIR / "monthly_performance.csv")
transactions = pd.read_csv(DATA_DIR / "transactions.csv")

monthly["reporting_month"] = pd.to_datetime(monthly["reporting_month"])
transactions["transaction_month"] = pd.to_datetime(
    transactions["transaction_month"]
)

# Aggregate account-month data into monthly portfolio KPIs
monthly_kpis = (
    monthly.groupby("reporting_month")
    .agg(
        active_accounts=("active", "sum"),
        total_purchase_spend=("purchase_spend", "sum"),
        total_outstanding_balance=("outstanding_balance", "sum"),
        total_credit_limit=("credit_limit", "sum"),
    )
    .reset_index()
)

# Portfolio utilization is a ratio of aggregate balances to aggregate limits
monthly_kpis["credit_utilization_pct"] = (
    monthly_kpis["total_outstanding_balance"]
    / monthly_kpis["total_credit_limit"]
    * 100
)

# Calculate month-over-month spending growth
monthly_kpis["spending_growth_pct"] = (
    monthly_kpis["total_purchase_spend"].pct_change() * 100
)

# Independently aggregate purchase transaction records
transaction_totals = (
    transactions.groupby("transaction_month")["amount"]
    .sum()
    .rename("transaction_purchase_total")
    .reset_index()
    .rename(columns={"transaction_month": "reporting_month"})
)

monthly_kpis = monthly_kpis.merge(
    transaction_totals,
    on="reporting_month",
    how="left",
)

monthly_kpis["transaction_purchase_total"] = (
    monthly_kpis["transaction_purchase_total"].fillna(0)
)

monthly_kpis["purchase_reconciliation_difference"] = (
    monthly_kpis["total_purchase_spend"]
    - monthly_kpis["transaction_purchase_total"]
)

monthly_kpis.to_csv(
    OUTPUT_DIR / "monthly_kpis.csv",
    index=False,
)

print("\nMONTHLY PORTFOLIO PERFORMANCE")
print(monthly_kpis.round(2).to_string(index=False))

print("\nMaximum absolute purchase reconciliation difference:")
print(
    monthly_kpis["purchase_reconciliation_difference"]
    .abs()
    .max()
)

print(f"\nKPI report saved to: {OUTPUT_DIR / 'monthly_kpis.csv'}")
