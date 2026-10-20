
import logging
import subprocess
import sys
from pathlib import Path

# Project directory
BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"
LOGS_DIR = BASE_DIR / "logs"

LOGS_DIR.mkdir(exist_ok=True)

# Save execution details to a log file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "pipeline.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

# Run scripts in dependency order.
# Each script must finish successfully before the next begins.
PIPELINE = [
    "generate_data.py",
    "validate_data.py",
    "calculate_kpis.py",
    "product_analysis.py",
    "monthly_product_analysis.py",
    "spending_change_analysis.py",
    "performance_alerts.py",
    "validation_framework.py",
    "build_database.py",
    "run_sql_queries.py",
]


def run_pipeline():
    logging.info("Starting Credit Card Portfolio Performance Intelligence pipeline.")

    for script in PIPELINE:
        script_path = SCRIPTS_DIR / script

        if not script_path.is_file():
            logging.error("Script not found: %s", script_path)
            raise FileNotFoundError(f"Missing pipeline script: {script_path}")

        logging.info("Running %s", script)

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=BASE_DIR,
            check=False,
        )

        if result.returncode != 0:
            logging.error(
                "Pipeline stopped: %s exited with code %s",
                script,
                result.returncode,
            )
            raise SystemExit(result.returncode)

        logging.info("Completed %s successfully.", script)

    logging.info("Pipeline completed successfully.")


if __name__ == "__main__":
    run_pipeline()
