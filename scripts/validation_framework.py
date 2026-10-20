
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

results = []


def record_check(layer, check_name, status, failed_rows, details):
    """Store one validation result in a consistent format."""
    results.append({
        "layer": layer,
        "check_name": check_name,
        "status": status,
        "failed_rows": int(failed_rows),
        "details": details,
    })


def load_csv(path, **kwargs):
    """Load a required CSV and raise a clear error if it is missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}\n"
            "Run the relevant data-generation or KPI script first."
        )
    return pd.read_csv(path, **kwargs)


def check_required_columns(df, required, dataset_name, layer):
    missing = sorted(set(required) - set(df.columns))

    record_check(
        layer,
        f"{dataset_name}: required columns",
        "PASS" if not missing else "FAIL",
        len(missing),
        "All required columns present."
        if not missing
        else f"Missing columns: {missing}",
    )


# ============================================================
# LOAD DATA
# ============================================================

accounts = load_csv(DATA_DIR / "accounts.csv")

monthly = load_csv(
    DATA_DIR / "monthly_performance.csv",
    parse_dates=["reporting_month"],
)

transactions = load_csv(
    DATA_DIR / "transactions.csv",
    parse_dates=["transaction_month"],
)

product_kpis = load_csv(
    OUTPUT_DIR / "monthly_product_kpis.csv",
    parse_dates=["reporting_month"],
)

portfolio_kpis = load_csv(
    OUTPUT_DIR / "monthly_kpis.csv",
    parse_dates=["reporting_month"],
)

# ============================================================
# LAYER 1: DATA QUALITY AND BUSINESS RULES
# ============================================================

layer = "Layer 1 - Data Quality"

check_required_columns(
    accounts,
    ["account_id", "product", "credit_limit"],
    "accounts",
    layer,
)

check_required_columns(
    monthly,
    [
        "account_id",
        "reporting_month",
        "active",
        "credit_limit",
        "outstanding_balance",
        "purchase_spend",
    ],
    "monthly_performance",
    layer,
)

check_required_columns(
    transactions,
    [
        "account_id",
        "transaction_month",
        "amount",
        "transaction_type",
    ],
    "transactions",
    layer,
)

# Continue with detailed checks only when required columns exist.
if {"account_id", "product", "credit_limit"}.issubset(accounts.columns):

    duplicate_accounts = accounts.duplicated(["account_id"]).sum()

    record_check(
        layer,
        "Unique account identifiers",
        "PASS" if duplicate_accounts == 0 else "FAIL",
        duplicate_accounts,
        "Each account must appear once in accounts.csv.",
    )

    invalid_limits = (
        accounts["credit_limit"].isna()
        | (accounts["credit_limit"] <= 0)
    ).sum()

    record_check(
        layer,
        "Valid account credit limits",
        "PASS" if invalid_limits == 0 else "FAIL",
        invalid_limits,
        "Credit limits must be present and greater than zero.",
    )

if {
    "account_id",
    "reporting_month",
    "active",
    "credit_limit",
    "outstanding_balance",
    "purchase_spend",
}.issubset(monthly.columns):

    duplicate_account_months = monthly.duplicated(
        ["account_id", "reporting_month"]
    ).sum()

    record_check(
        layer,
        "Unique account-month records",
        "PASS" if duplicate_account_months == 0 else "FAIL",
        duplicate_account_months,
        "Each account must have at most one record per month.",
    )

    missing_identifiers = (
        monthly["account_id"].isna()
        | monthly["reporting_month"].isna()
    ).sum()

    record_check(
        layer,
        "Missing account or month identifiers",
        "PASS" if missing_identifiers == 0 else "FAIL",
        missing_identifiers,
        "Account ID and reporting month must be populated.",
    )

    negative_spend = (
        monthly["purchase_spend"].isna()
        | (monthly["purchase_spend"] < 0)
    ).sum()

    record_check(
        layer,
        "Non-negative purchase spending",
        "PASS" if negative_spend == 0 else "FAIL",
        negative_spend,
        "Purchase spending must be present and non-negative.",
    )

    invalid_balances = (
        monthly["outstanding_balance"].isna()
        | (monthly["outstanding_balance"] < 0)
    ).sum()

    record_check(
        layer,
        "Non-negative outstanding balances",
        "PASS" if invalid_balances == 0 else "FAIL",
        invalid_balances,
        "Outstanding balances must be present and non-negative.",
    )

    invalid_monthly_limits = (
        monthly["credit_limit"].isna()
        | (monthly["credit_limit"] <= 0)
    ).sum()

    record_check(
        layer,
        "Valid monthly credit limits",
        "PASS" if invalid_monthly_limits == 0 else "FAIL",
        invalid_monthly_limits,
        "Monthly credit limits must be present and positive.",
    )

    # Allow a small tolerance for floating-point representation.
    over_limit = (
        monthly["outstanding_balance"]
        > monthly["credit_limit"] + 0.01
    ).sum()

    record_check(
        layer,
        "Outstanding balance does not exceed credit limit",
        "PASS" if over_limit == 0 else "FAIL",
        over_limit,
        "Snapshot balances must not exceed the recorded credit limit.",
    )

    invalid_active_flags = (
        monthly["active"].isna()
        | ~monthly["active"].isin([True, False, 0, 1])
    ).sum()

    record_check(
        layer,
        "Valid active-account flags",
        "PASS" if invalid_active_flags == 0 else "FAIL",
        invalid_active_flags,
        "Active status must be Boolean or encoded as 0/1.",
    )

# Check that transaction amounts are valid.
if {"amount", "account_id", "transaction_month"}.issubset(
    transactions.columns
):
    invalid_transactions = (
        transactions["amount"].isna()
        | (transactions["amount"] < 0)
        | transactions["account_id"].isna()
        | transactions["transaction_month"].isna()
    ).sum()

    record_check(
        layer,
        "Valid transaction records",
        "PASS" if invalid_transactions == 0 else "FAIL",
        invalid_transactions,
        "Transaction amount must be non-negative, with account and month present.",
    )

# ============================================================
# LAYER 2: METRIC RECONCILIATION
# ============================================================

layer = "Layer 2 - Metric Reconciliation"

product_required = {
    "reporting_month",
    "product",
    "total_purchase_spend",
}

portfolio_required = {
    "reporting_month",
    "total_purchase_spend",
}

if (
    product_required.issubset(product_kpis.columns)
    and portfolio_required.issubset(portfolio_kpis.columns)
):

    # Check for duplicate month-product and portfolio-month rows.
    duplicate_product_rows = product_kpis.duplicated(
        ["reporting_month", "product"]
    ).sum()

    record_check(
        layer,
        "Unique month-product KPI rows",
        "PASS" if duplicate_product_rows == 0 else "FAIL",
        duplicate_product_rows,
        "Each product should have one KPI row per month.",
    )

    duplicate_portfolio_rows = portfolio_kpis.duplicated(
        ["reporting_month"]
    ).sum()

    record_check(
        layer,
        "Unique portfolio-month KPI rows",
        "PASS" if duplicate_portfolio_rows == 0 else "FAIL",
        duplicate_portfolio_rows,
        "The portfolio should have one KPI row per month.",
    )

    # Sum product spending independently and compare with portfolio KPIs.
    product_totals = (
        product_kpis.groupby("reporting_month")["total_purchase_spend"]
        .sum()
        .rename("product_total")
    )

    portfolio_totals = (
        portfolio_kpis.set_index("reporting_month")["total_purchase_spend"]
        .rename("portfolio_total")
    )

    comparison = pd.concat(
        [product_totals, portfolio_totals],
        axis=1,
        join="outer",
    )

    tolerance = 0.02

    mismatch = (
        comparison["product_total"].isna()
        | comparison["portfolio_total"].isna()
        | (
            comparison["product_total"]
            - comparison["portfolio_total"]
        ).abs().gt(tolerance)
    )

    record_check(
        layer,
        "Product-to-portfolio spending reconciliation",
        "PASS" if not mismatch.any() else "FAIL",
        mismatch.sum(),
        (
            "Product spending totals agree with portfolio totals "
            f"within ₹{tolerance:.2f}."
            if not mismatch.any()
            else "One or more monthly totals do not reconcile."
        ),
    )

# Check purchase transactions against the monthly spending dataset.
if {
    "account_id",
    "reporting_month",
    "purchase_spend",
}.issubset(monthly.columns) and {
    "account_id",
    "transaction_month",
    "amount",
    "transaction_type",
}.issubset(transactions.columns):

    purchase_transactions = transactions.loc[
        transactions["transaction_type"].eq("PURCHASE")
    ]

    monthly_purchase_total = monthly["purchase_spend"].sum()
    transaction_purchase_total = purchase_transactions["amount"].sum()

    difference = abs(
        monthly_purchase_total - transaction_purchase_total
    )

    record_check(
        layer,
        "Monthly spending versus purchase transaction total",
        "PASS" if difference <= 0.02 else "FAIL",
        0 if difference <= 0.02 else 1,
        (
            f"Absolute difference: ₹{difference:.4f}. "
            "This is a consistency check because both datasets "
            "were generated from the same synthetic source."
        ),
    )

# ============================================================
# LAYER 3: STATISTICAL ANOMALY DETECTION
# ============================================================

layer = "Layer 3 - Statistical Anomaly Detection"

if product_required.issubset(product_kpis.columns):

    anomaly_data = product_kpis[
        ["reporting_month", "product", "total_purchase_spend"]
    ].copy()

    anomaly_data = anomaly_data.sort_values(
        ["product", "reporting_month"]
    )

    anomaly_data["monthly_change_pct"] = (
        anomaly_data.groupby("product")["total_purchase_spend"]
        .pct_change()
        .mul(100)
    )

    # Robust Z-score using median absolute deviation (MAD).
    # First month has no prior month and is not assessed.
    anomaly_data["robust_z_score"] = np.nan

    for product_name, group in anomaly_data.groupby("product"):
        valid_changes = group["monthly_change_pct"].dropna()

        if len(valid_changes) < 5:
            continue

        median_change = valid_changes.median()
        mad = (valid_changes - median_change).abs().median()

        if mad > 0:
            robust_z = (
                0.6745 * (valid_changes - median_change) / mad
            )
            anomaly_data.loc[
                robust_z.index, "robust_z_score"
            ] = robust_z

    anomaly_data["anomaly_flag"] = (
        anomaly_data["robust_z_score"].abs() > 3.5
    )

    anomaly_rows = anomaly_data.loc[
        anomaly_data["anomaly_flag"]
    ].copy()

    anomaly_output = OUTPUT_DIR / "statistical_anomalies.csv"
    anomaly_data.to_csv(anomaly_output, index=False)

    record_check(
        layer,
        "Unusual product spending movements",
        "REVIEW" if not anomaly_rows.empty else "PASS",
        len(anomaly_rows),
        (
            f"{len(anomaly_rows)} unusual movement(s) flagged for review. "
            "Statistical anomalies are warnings, not proof of data errors."
            if not anomaly_rows.empty
            else "No movements exceeded the robust Z-score threshold."
        ),
    )

# ============================================================
# SAVE AND DISPLAY THE VALIDATION REPORT
# ============================================================

report = pd.DataFrame(results)

report_path = OUTPUT_DIR / "validation_report.csv"
report.to_csv(report_path, index=False)

print("\nTHREE-LAYER VALIDATION REPORT")
print("=" * 90)

if report.empty:
    print("No checks were executed. Review the required input columns.")
else:
    print(report.to_string(index=False))

print("\nSUMMARY")
print("-" * 40)

if not report.empty:
    print(f"Checks executed: {len(report)}")
    print(f"PASS: {(report['status'] == 'PASS').sum()}")
    print(f"FAIL: {(report['status'] == 'FAIL').sum()}")
    print(f"REVIEW: {(report['status'] == 'REVIEW').sum()}")

print(f"\nValidation report saved to: {report_path}")
print(f"Statistical anomaly output: {OUTPUT_DIR / 'statistical_anomalies.csv'}")

if not report.empty and (report["status"] == "FAIL").any():
    print("\nWARNING: Resolve FAIL results before publishing the dashboard.")

