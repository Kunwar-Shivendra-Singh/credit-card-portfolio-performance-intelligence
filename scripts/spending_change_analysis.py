
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# 1. Set up project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = OUTPUT_DIR / "monthly_product_kpis.csv"

# --------------------------------------------------
# 2. Load and validate input data
# --------------------------------------------------

data = pd.read_csv(
    INPUT_FILE,
    parse_dates=["reporting_month"],
)

required_columns = {
    "reporting_month",
    "product",
    "total_purchase_spend",
}

missing_columns = required_columns - set(data.columns)

if missing_columns:
    raise ValueError(
        f"Missing required columns: {sorted(missing_columns)}"
    )

if data.duplicated(["reporting_month", "product"]).any():
    raise ValueError(
        "Duplicate reporting_month-product combinations found."
    )

data = data.sort_values(
    ["product", "reporting_month"]
).reset_index(drop=True)

# --------------------------------------------------
# 3. Calculate product-level spending changes
# --------------------------------------------------

data["previous_product_spend"] = (
    data.groupby("product")["total_purchase_spend"].shift(1)
)

data["product_spend_change"] = (
    data["total_purchase_spend"]
    - data["previous_product_spend"]
)

# --------------------------------------------------
# 4. Calculate portfolio-level monthly changes
# --------------------------------------------------

portfolio = (
    data.groupby("reporting_month", as_index=False)
    .agg(
        total_purchase_spend=("total_purchase_spend", "sum")
    )
    .sort_values("reporting_month")
    .reset_index(drop=True)
)

portfolio["previous_month_spend"] = (
    portfolio["total_purchase_spend"].shift(1)
)

portfolio["spend_change"] = (
    portfolio["total_purchase_spend"]
    - portfolio["previous_month_spend"]
)

portfolio["spend_growth_pct"] = (
    portfolio["total_purchase_spend"].pct_change() * 100
)

# --------------------------------------------------
# 5. Attach portfolio changes to product records
# --------------------------------------------------

data = data.merge(
    portfolio[
        [
            "reporting_month",
            "previous_month_spend",
            "spend_change",
            "spend_growth_pct",
        ]
    ],
    on="reporting_month",
    how="left",
    validate="many_to_one",
)

# --------------------------------------------------
# 6. Calculate product contributions
# --------------------------------------------------

# Sum of absolute product changes for each month.
# This measures the total magnitude of product movements.

absolute_product_changes = (
    data.groupby("reporting_month")["product_spend_change"]
    .transform(lambda changes: changes.abs().sum())
)

data["relative_movement_pct"] = (
    data["product_spend_change"]
    / absolute_product_changes.where(
        absolute_product_changes != 0
    )
    * 100
)

# Net contribution: product change relative to the
# portfolio's overall net change. This can exceed 100%
# or be negative when products offset one another.

data["net_change_contribution_pct"] = (
    data["product_spend_change"]
    / data["spend_change"].where(data["spend_change"] != 0)
    * 100
)

# --------------------------------------------------
# 7. Check reconciliation of product changes
# --------------------------------------------------

product_change_totals = (
    data.groupby("reporting_month", as_index=False)
    .agg(
        sum_product_changes=("product_spend_change", "sum")
    )
)

portfolio = portfolio.merge(
    product_change_totals,
    on="reporting_month",
    how="left",
    validate="one_to_one",
)

portfolio["change_reconciliation_difference"] = (
    portfolio["sum_product_changes"]
    - portfolio["spend_change"]
)

# --------------------------------------------------
# 8. Save output files
# --------------------------------------------------

detail_output = OUTPUT_DIR / "spending_change_analysis.csv"
portfolio_output = OUTPUT_DIR / "portfolio_spending_trend.csv"

data.to_csv(detail_output, index=False)
portfolio.to_csv(portfolio_output, index=False)

# --------------------------------------------------
# 9. Print results
# --------------------------------------------------

print("\nPORTFOLIO SPENDING TREND")
print(portfolio.round(2).to_string(index=False))

latest_month = data["reporting_month"].max()

print(f"\nPRODUCT CONTRIBUTIONS FOR {latest_month:%B %Y}")

latest = data.loc[
    data["reporting_month"] == latest_month,
    [
        "product",
        "product_spend_change",
        "spend_change",
        "spend_growth_pct",
        "relative_movement_pct",
        "net_change_contribution_pct",
    ],
]

print(latest.round(2).to_string(index=False))

max_difference = portfolio[
    "change_reconciliation_difference"
].abs().max()

print("\nVALIDATION")
print(f"Maximum change reconciliation difference: {max_difference:.10f}")

print("\nFILES SAVED")
print(detail_output)
print(portfolio_output)

