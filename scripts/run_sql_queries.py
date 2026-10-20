
from pathlib import Path
import sqlite3

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "portfolio.db"
SQL_FILE = PROJECT_ROOT / "sql" / "sql_queries.sql"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not DB_PATH.exists():
    raise FileNotFoundError(f"Database not found: {DB_PATH}")

if not SQL_FILE.exists():
    raise FileNotFoundError(f"SQL file not found: {SQL_FILE}")

sql_text = SQL_FILE.read_text(encoding="utf-8")

# Each query is separated by a semicolon.
queries = [
    statement.strip()
    for statement in sql_text.split(";")
    if statement.strip()
]

if len(queries) != 5:
    raise ValueError(
        f"Expected 5 SQL queries, found {len(queries)}."
    )

with sqlite3.connect(DB_PATH) as connection:
    for index, query in enumerate(queries, start=1):
        result = pd.read_sql_query(query, connection)

        output_path = OUTPUT_DIR / f"sql_result_{index}.csv"
        result.to_csv(output_path, index=False)

        print(f"\nQUERY {index}")
        print("=" * 70)
        print(result.head(12).to_string(index=False))
        print(f"\nRows returned: {len(result):,}")
        print(f"Saved: {output_path}")

print("\nAll SQL queries executed successfully.")
