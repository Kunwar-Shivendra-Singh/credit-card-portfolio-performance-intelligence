
import sqlite3
import unittest
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
DB_PATH = BASE_DIR / "portfolio.db"


class TestPortfolioPipeline(unittest.TestCase):

    def test_accounts_have_unique_ids(self):
        accounts = pd.read_csv(DATA_DIR / "accounts.csv")

        self.assertEqual(
            accounts["account_id"].nunique(),
            len(accounts),
        )

    def test_monthly_performance_has_unique_account_months(self):
        monthly = pd.read_csv(DATA_DIR / "monthly_performance.csv")

        self.assertFalse(
            monthly.duplicated(
                ["account_id", "reporting_month"]
            ).any()
        )

    def test_monthly_kpis_cover_12_months(self):
        kpis = pd.read_csv(OUTPUT_DIR / "monthly_kpis.csv")

        self.assertEqual(len(kpis), 12)
        self.assertEqual(
            kpis["reporting_month"].nunique(),
            12,
        )

    def test_purchase_spending_is_nonnegative(self):
        monthly = pd.read_csv(DATA_DIR / "monthly_performance.csv")

        self.assertTrue(
            (monthly["purchase_spend"] >= 0).all()
        )

    def test_product_kpis_have_36_rows(self):
        product_kpis = pd.read_csv(
            OUTPUT_DIR / "monthly_product_kpis.csv"
        )

        self.assertEqual(len(product_kpis), 36)
        self.assertEqual(
            product_kpis["product"].nunique(),
            3,
        )

    def test_alerts_contain_expected_months_and_types(self):
        alerts = pd.read_csv(
            OUTPUT_DIR / "performance_alerts.csv"
        )

        # Keep only rows classified as significant alerts.
        actual_alerts = alerts[
            alerts["alert_type"].isin(
                ["LARGE_DECREASE", "LARGE_INCREASE"]
            )
        ]

        self.assertEqual(
            set(actual_alerts["reporting_month"]),
            {"2025-09-01", "2025-10-01"},
        )

        self.assertEqual(
            set(actual_alerts["alert_type"]),
            {"LARGE_DECREASE", "LARGE_INCREASE"},
        )

    def test_sql_spending_reconciliation_is_zero(self):
        result = pd.read_csv(
            OUTPUT_DIR / "sql_result_5.csv"
        )

        differences = result["reconciliation_difference"]

        self.assertTrue(
            differences.abs().le(0.02).all()
        )

    def test_database_tables_exist(self):
        self.assertTrue(DB_PATH.exists())

        with sqlite3.connect(DB_PATH) as connection:
            tables = pd.read_sql_query(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """,
                connection,
            )["name"].tolist()

        expected_tables = {
            "accounts",
            "monthly_performance",
            "transactions",
        }

        self.assertTrue(
            expected_tables.issubset(set(tables))
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

