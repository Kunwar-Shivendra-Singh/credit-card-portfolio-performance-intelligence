# Credit Card Portfolio Performance Intelligence System

A Python, SQL, and Power BI analytics project designed to monitor credit card portfolio performance, evaluate product-level spending trends, reconcile key metrics, and flag significant changes in customer spending.

> **Data disclosure:** This project uses synthetic data generated for analytical and educational purposes. It does not contain real customer records or represent the performance of an actual financial institution.

## Business Problem

Credit card portfolio teams need a consistent view of purchase spending, active accounts, credit utilization, and product-level performance. Significant movements in spending can be obscured by aggregate portfolio trends.

This project develops a reproducible analytics workflow to:

- Monitor monthly portfolio performance.
- Compare Classic, Gold, and Platinum card products.
- Calculate month-over-month spending changes.
- Flag significant product-level spending movements.
- Validate data quality and reconcile analytical outputs.
- Present results in an interactive Power BI dashboard.

## Project Highlights

- Generated a synthetic dataset containing **10,000 accounts**.
- Created **120,000 account-month records** covering January–December 2025.
- Generated **114,044 purchase transaction records**.
- Built Python workflows for data generation, validation, KPI calculation, and alert generation.
- Stored source data in SQLite and executed five analytical SQL queries.
- Implemented a three-layer validation framework.
- Developed a Power BI dashboard with KPI cards, monthly spending trends, product comparisons, an alert table, and a reporting-month slicer.
- Added eight automated tests using Python's `unittest` framework.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data generation, transformation, validation, KPI calculation, and automation |
| Pandas and NumPy | Data manipulation and numerical analysis |
| SQL | Portfolio analysis, product comparisons, and spending reconciliation |
| SQLite | Relational storage of accounts, monthly performance, and transactions |
| Power BI | Interactive reporting and visualization |
| unittest | Automated testing |

## Data Model

### Accounts

Contains account-level attributes, including account identifiers, card products, and credit limits.

### Monthly Performance

Contains monthly account-level activity, purchase spending, outstanding balances, credit limits, and active-account status.

### Transactions

Contains synthetic purchase transaction records associated with accounts and transaction months.

The three source tables are loaded into `portfolio.db`.

## Analytical Workflow

1. **Generate data:** Create synthetic account, monthly performance, and purchase transaction datasets.
2. **Validate source data:** Check required fields, duplicates, missing values, and business rules.
3. **Calculate portfolio KPIs:** Measure active accounts, purchase spending, outstanding balances, credit limits, and credit utilization.
4. **Analyze products:** Compare Classic, Gold, and Platinum performance at portfolio and monthly levels.
5. **Analyze spending changes:** Calculate month-over-month changes and product contributions.
6. **Generate alerts:** Flag product-level spending movements that exceed the configured threshold.
7. **Run validation checks:** Evaluate data quality, metric reconciliation, and statistical anomalies.
8. **Build the database:** Load the source datasets into SQLite.
9. **Execute SQL analysis:** Generate portfolio trends, product summaries, and reconciliation outputs.
10. **Run automated tests:** Verify core data, output, alert, and database expectations.

## Key Analytical Findings

The synthetic scenario produces the following results:

- **September 2025:** Portfolio purchase spending decreased by approximately 2.23% month over month.
- **Platinum, September 2025:** Purchase spending decreased by approximately 14.69%, triggering a `LARGE_DECREASE` alert.
- **October 2025:** Portfolio purchase spending increased by approximately 4.49% month over month.
- **Platinum, October 2025:** Purchase spending increased by approximately 20.58%, triggering a `LARGE_INCREASE` alert.

These movements are deliberately simulated and should not be interpreted as observed market or bank performance.

## Data Quality and Validation

The validation framework reports:

- **18 checks executed**
- **17 PASS**
- **0 FAIL**
- **1 REVIEW**

The review status identifies unusual product spending movements for further investigation. It is a statistical warning, not proof of a data error.

Purchase-spending totals reconcile across the generated monthly performance and transaction datasets. Because both are generated from the same synthetic source, this is a consistency check rather than an independent accounting reconciliation.

## Power BI Dashboard

The dashboard includes:

- Purchase Spending KPI
- Active Accounts KPI
- Credit Utilization KPI
- Monthly portfolio purchase-spending trend
- Monthly spending comparison by card product
- Performance alert table
- Reporting-month slicer

The reporting-month slicer filters the KPI cards and alert table while the trend charts retain the full January–December 2025 series.


## Project Structure

```text
credit-card-performance-intelligence/
├── data/
├── logs/
├── outputs/
├── scripts/
├── sql/
├── tests/
│   └── test_pipeline.py
├── main.py
├── portfolio.db
├── requirements.txt
└── README.md
```

- `data/`: Generated source datasets.
- `scripts/`: Data generation, validation, analytics, database, and SQL execution scripts.
- `outputs/`: KPI reports, alerts, validation reports, and SQL result files.
- `sql/`: Analytical SQL queries.
- `logs/`: Pipeline execution logs.
- `tests/`: Automated tests.
- `main.py`: Pipeline entry point.
- `portfolio.db`: SQLite database.
- `requirements.txt`: Python package dependencies.

## How to Run

### 1. Install Python

Install a compatible Python version and verify that Python is available in your terminal.

### 2. Install dependencies

From the project root, run:

```bash
py -m pip install -r requirements.txt
```

### 3. Run the pipeline

```bash
py main.py
```

The pipeline executes the configured scripts sequentially and records execution details in `logs/pipeline.log`.

### 4. Run automated tests

```bash
py -m unittest discover -s tests -v
```

The current test suite contains eight tests covering core data quality, output expectations, alert classifications, SQL reconciliation, and database tables.

## Limitations and Future Improvements

- The data is synthetic and does not establish real-world customer behavior.
- Statistical alerts identify movements for review; they do not establish causation.
- Transaction reconciliation is not independent because the datasets share a generated source.
- Future work could include stronger integration tests, configurable alert thresholds, more granular transaction analysis, and additional portfolio risk metrics.

## Author

Developed as a portfolio project demonstrating Python-based data analytics, SQL, data quality validation, workflow automation, and Power BI reporting.