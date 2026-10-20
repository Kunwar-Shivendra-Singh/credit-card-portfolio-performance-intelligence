
-- =========================================================
-- QUERY 1: Monthly portfolio performance
-- =========================================================

SELECT
    reporting_month,
    COUNT(*) AS account_months,
    SUM(CASE WHEN active = 1 THEN 1 ELSE 0 END) AS active_accounts,
    ROUND(SUM(purchase_spend), 2) AS total_purchase_spend,
    ROUND(SUM(outstanding_balance), 2) AS total_outstanding_balance,
    ROUND(SUM(credit_limit), 2) AS total_credit_limit,
    ROUND(
        100.0 * SUM(outstanding_balance)
        / NULLIF(SUM(credit_limit), 0),
        2
    ) AS credit_utilization_pct
FROM monthly_performance
GROUP BY reporting_month
ORDER BY reporting_month;


-- =========================================================
-- QUERY 2: Product-level performance
-- =========================================================

SELECT
    a.product,
    COUNT(*) AS account_months,
    SUM(CASE WHEN m.active = 1 THEN 1 ELSE 0 END) AS active_account_months,
    ROUND(SUM(m.purchase_spend), 2) AS total_purchase_spend,
    ROUND(SUM(m.outstanding_balance), 2) AS total_outstanding_balance,
    ROUND(
        100.0 * SUM(m.outstanding_balance)
        / NULLIF(SUM(m.credit_limit), 0),
        2
    ) AS credit_utilization_pct
FROM monthly_performance AS m
JOIN accounts AS a
    ON m.account_id = a.account_id
GROUP BY a.product
ORDER BY total_purchase_spend DESC;


-- =========================================================
-- QUERY 3: Month-on-month portfolio spending growth
-- =========================================================

WITH monthly_totals AS (
    SELECT
        reporting_month,
        SUM(purchase_spend) AS total_purchase_spend
    FROM monthly_performance
    GROUP BY reporting_month
),
monthly_comparison AS (
    SELECT
        reporting_month,
        total_purchase_spend,
        LAG(total_purchase_spend) OVER (
            ORDER BY reporting_month
        ) AS previous_month_spend
    FROM monthly_totals
)
SELECT
    reporting_month,
    ROUND(total_purchase_spend, 2) AS total_purchase_spend,
    ROUND(previous_month_spend, 2) AS previous_month_spend,
    ROUND(
        total_purchase_spend - previous_month_spend,
        2
    ) AS spend_change,
    ROUND(
        100.0 * (total_purchase_spend - previous_month_spend)
        / NULLIF(previous_month_spend, 0),
        2
    ) AS spend_growth_pct
FROM monthly_comparison
ORDER BY reporting_month;


-- =========================================================
-- QUERY 4: Product-level monthly spending changes
-- =========================================================

WITH product_monthly AS (
    SELECT
        a.product,
        m.reporting_month,
        SUM(m.purchase_spend) AS total_purchase_spend
    FROM monthly_performance AS m
    JOIN accounts AS a
        ON m.account_id = a.account_id
    GROUP BY
        a.product,
        m.reporting_month
),
product_comparison AS (
    SELECT
        product,
        reporting_month,
        total_purchase_spend,
        LAG(total_purchase_spend) OVER (
            PARTITION BY product
            ORDER BY reporting_month
        ) AS previous_month_spend
    FROM product_monthly
)
SELECT
    product,
    reporting_month,
    ROUND(total_purchase_spend, 2) AS total_purchase_spend,
    ROUND(previous_month_spend, 2) AS previous_month_spend,
    ROUND(
        100.0 * (total_purchase_spend - previous_month_spend)
        / NULLIF(previous_month_spend, 0),
        2
    ) AS spend_growth_pct
FROM product_comparison
ORDER BY product, reporting_month;


-- =========================================================
-- QUERY 5: Monthly purchase transaction reconciliation
-- =========================================================

WITH transaction_totals AS (
    SELECT
        transaction_month,
        SUM(amount) AS transaction_spend
    FROM transactions
    WHERE transaction_type = 'PURCHASE'
    GROUP BY transaction_month
),
monthly_totals AS (
    SELECT
        reporting_month,
        SUM(purchase_spend) AS monthly_spend
    FROM monthly_performance
    GROUP BY reporting_month
)
SELECT
    m.reporting_month,
    ROUND(m.monthly_spend, 2) AS monthly_spend,
    ROUND(COALESCE(t.transaction_spend, 0), 2) AS transaction_spend,
    ROUND(
        m.monthly_spend - COALESCE(t.transaction_spend, 0),
        2
    ) AS reconciliation_difference
FROM monthly_totals AS m
LEFT JOIN transaction_totals AS t
    ON m.reporting_month = t.transaction_month
ORDER BY m.reporting_month;

