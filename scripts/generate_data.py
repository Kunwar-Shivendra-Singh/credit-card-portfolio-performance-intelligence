
from pathlib import Path

import numpy as np
import pandas as pd


# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

SEED = 42
rng = np.random.default_rng(SEED)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

N_ACCOUNTS = 10_000
MONTHS = pd.date_range("2025-01-01", periods=12, freq="MS")

PRODUCTS = ["Classic", "Gold", "Platinum"]
PRODUCT_PROBABILITIES = [0.50, 0.35, 0.15]

# Monthly spending growth assumptions.
# These are simulation assumptions, not real bank estimates.
PRODUCT_GROWTH = {
    "Classic": 0.010,
    "Gold": 0.015,
    "Platinum": 0.020,
}

BASE_SPENDING = {
    "Classic": 1600.0,
    "Gold": 2250.0,
    "Platinum": 2900.0,
}

# Simulated business event:
# Platinum spending falls by 15% in September 2025.
SHOCK_MONTH = pd.Timestamp("2025-09-01")
SHOCK_PRODUCT = "Platinum"
SHOCK_FACTOR = 0.85


# --------------------------------------------------
# 2. Generate account-level records
# --------------------------------------------------

account_ids = np.arange(100001, 100001 + N_ACCOUNTS)

product = rng.choice(
    PRODUCTS,
    size=N_ACCOUNTS,
    p=PRODUCT_PROBABILITIES,
)

limit_ranges = {
    "Classic": (20_000, 80_001),
    "Gold": (50_000, 200_001),
    "Platinum": (100_000, 500_001),
}

credit_limits = np.array([
    rng.integers(*limit_ranges[p]) for p in product
])

accounts = pd.DataFrame({
    "account_id": account_ids,
    "product": product,
    "credit_limit": credit_limits,
})


# --------------------------------------------------
# 3. Generate monthly performance
# --------------------------------------------------

monthly_records = []

# Account-level spending variation remains consistent
# across months to avoid completely independent draws.
account_spending_factor = rng.lognormal(
    mean=0.0,
    sigma=0.25,
    size=N_ACCOUNTS,
)

account_utilization_factor = rng.beta(
    a=2,
    b=5,
    size=N_ACCOUNTS,
)

for month_index, month in enumerate(MONTHS):

    # Stable 95% monthly activity probability.
    # Monthly active status is simulated independently.
    active = rng.random(N_ACCOUNTS) >= 0.05

    product_growth = np.array([
        (1 + PRODUCT_GROWTH[p]) ** month_index
        for p in product
    ])

    base_spending = np.array([
        BASE_SPENDING[p] for p in product
    ])

    spending = (
        base_spending
        * account_spending_factor
        * product_growth
        * rng.lognormal(mean=0.0, sigma=0.08, size=N_ACCOUNTS)
    )

    # Apply the controlled synthetic event.
    if month == SHOCK_MONTH:
        spending = np.where(
            product == SHOCK_PRODUCT,
            spending * SHOCK_FACTOR,
            spending,
        )

    spending = np.where(active, spending, 0.0)
    spending = np.round(spending, 2)

    # Simplified balance snapshots.
    # These are not derived from transaction/payment ledgers.
    utilization = np.clip(
        account_utilization_factor
        + rng.normal(0, 0.015, size=N_ACCOUNTS),
        0.01,
        0.95,
    )

    balances = np.round(credit_limits * utilization, 2)

    monthly_records.append(pd.DataFrame({
        "account_id": account_ids,
        "reporting_month": month,
        "active": active,
        "credit_limit": credit_limits,
        "outstanding_balance": balances,
        "purchase_spend": spending,
    }))

monthly_performance = pd.concat(
    monthly_records,
    ignore_index=True,
)


# --------------------------------------------------
# 4. Create purchase records from monthly spending
# --------------------------------------------------

transactions = monthly_performance.loc[
    monthly_performance["purchase_spend"] > 0,
    ["account_id", "reporting_month", "purchase_spend"],
].copy()

transactions = transactions.rename(columns={
    "reporting_month": "transaction_month",
    "purchase_spend": "amount",
})

transactions["transaction_type"] = "PURCHASE"


# --------------------------------------------------
# 5. Save datasets
# --------------------------------------------------

accounts.to_csv(DATA_DIR / "accounts.csv", index=False)

monthly_performance.to_csv(
    DATA_DIR / "monthly_performance.csv",
    index=False,
)

transactions.to_csv(
    DATA_DIR / "transactions.csv",
    index=False,
)


# --------------------------------------------------
# 6. Report generation summary
# --------------------------------------------------

print("Synthetic data generation completed.")
print(f"Accounts: {len(accounts):,}")
print(f"Monthly records: {len(monthly_performance):,}")
print(f"Purchase records: {len(transactions):,}")
print(f"Reporting period: {MONTHS.min():%b %Y} to {MONTHS.max():%b %Y}")
print(
    f"Simulated event: {SHOCK_PRODUCT} spending reduced by "
    f"{(1 - SHOCK_FACTOR) * 100:.0f}% in {SHOCK_MONTH:%B %Y}"
)
print(f"Output directory: {DATA_DIR}")


