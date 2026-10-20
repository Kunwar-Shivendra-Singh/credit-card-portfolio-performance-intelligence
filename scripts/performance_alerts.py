
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"

INPUT_FILE = OUTPUT_DIR / "monthly_product_kpis.csv"
OUTPUT_FILE = OUTPUT_DIR / "performance_alerts.csv"

# Flag changes whose absolute value reaches this threshold.
# This is a configurable demonstration rule, not a bank policy.
CHANGE_THRESHOLD_PCT = 10.0


# --------------------------------------------------
# 2. Load monthly product data
# --------------------------------------------------

data = pd.read_csv(
    INPUT_FILE,
    parse_dates=["reporting_month"],
)

data = data.sort_values(
    ["product", "reporting_month"]
).copy()

# --------------------------------------------------
# 3. Calculate month-over-month changes
# --------------------------------------------------

data["previous_month_spend"] = (
    data.groupby("product")["total_purchase_spend"].shift(1)
)

data["spend_change"] = (
    data["total_purchase_spend"]
    - data["previous_month_spend"]
)

data["spend_change_pct"] = (
    data["spend_change"]
    / data["previous_month_spend"].where(
        data["previous_month_spend"] != 0
    )
    * 100
)

# --------------------------------------------------
# 4. Flag large product-level changes
# --------------------------------------------------

data["alert_flag"] = (
    data["spend_change_pct"].abs() >= CHANGE_THRESHOLD_PCT
)

data["alert_type"] = "NO_ALERT"

data.loc[
    data["spend_change_pct"] >= CHANGE_THRESHOLD_PCT,
    "alert_type",
] = "LARGE_INCREASE"

data.loc[
    data["spend_change_pct"] <= -CHANGE_THRESHOLD_PCT,
    "alert_type",
] = "LARGE_DECREASE"

# --------------------------------------------------
# 5. Add portfolio-level context
# --------------------------------------------------

portfolio = (
    data.groupby("reporting_month", as_index=False)
    .agg(
        portfolio_spend=("total_purchase_spend", "sum")
    )
    .sort_values("reporting_month")
)

portfolio["previous_portfolio_spend"] = (
    portfolio["portfolio_spend"].shift(1)
)

portfolio["portfolio_change"] = (
    portfolio["portfolio_spend"]
    - portfolio["previous_portfolio_spend"]
)

portfolio["portfolio_change_pct"] = (
    portfolio["portfolio_change"]
    / portfolio["previous_portfolio_spend"].where(
        portfolio["previous_portfolio_spend"] != 0
    )
    * 100
)

data = data.merge(
    portfolio[
        [
            "reporting_month",
            "portfolio_spend",
            "portfolio_change",
            "portfolio_change_pct",
        ]
    ],
    on="reporting_month",
    how="left",
    validate="many_to_one",
)

# --------------------------------------------------
# 6. Save and display the report
# --------------------------------------------------

data.to_csv(OUTPUT_FILE, index=False)

alerts = data.loc[
    data["alert_flag"],
    [
        "reporting_month",
        "product",
        "previous_month_spend",
        "total_purchase_spend",
        "spend_change",
        "spend_change_pct",
        "portfolio_change_pct",
        "alert_type",
    ],
]

print("\nPERFORMANCE ALERTS")

if alerts.empty:
    print("No product spending changes exceeded the threshold.")
else:
    print(alerts.round(2).to_string(index=False))

print(f"\nAlert threshold: +/-{CHANGE_THRESHOLD_PCT:.1f}%")
print(f"Report saved to: {OUTPUT_FILE}")

