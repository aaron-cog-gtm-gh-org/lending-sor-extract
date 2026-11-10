import json
from pathlib import Path

from db import connect

ROOT = Path(__file__).resolve().parent


def run():
    config = json.loads((ROOT / "config.json").read_text())
    with connect() as db:
        db.execute("""
            CREATE OR REPLACE TABLE sor_loans AS
            SELECT loan_id, client_id, product_code, currency,
                   balance::DECIMAL(18,2) AS balance,
                   balance_usd::DECIMAL(18,2) AS balance_usd,
                   status, booking_date::DATE AS booking_date
            FROM read_csv_auto(?)
        """, [str(ROOT / "data/sor_loans.csv")])
        db.execute("""
            CREATE OR REPLACE TABLE stg_loans AS
            SELECT * FROM sor_loans
            WHERE status != 'CLOSED'
              AND booking_date <= ?::DATE
        """, [config["cutoff_date"]])


if __name__ == "__main__":
    run()
