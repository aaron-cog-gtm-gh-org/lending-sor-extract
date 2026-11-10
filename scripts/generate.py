import csv
import random
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RATES = {"USD": Decimal("1.0000"), "GBP": Decimal("1.2734"), "EUR": Decimal("1.0847")}


def generate():
    rng = random.Random(73021)
    with (ROOT / "data/sor_loans.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["loan_id", "client_id", "product_code", "currency",
                         "balance", "balance_usd", "status", "booking_date"])
        for i in range(1, 201):
            client = 1 + (i - 29) % 3 if 29 <= i <= 37 else 4 + (i % 22)
            currency = ("GBP" if i % 2 else "EUR") if 11 <= i <= 28 else "USD"
            balance = Decimal(rng.randrange(1000000, 50000000)) / 100
            usd = (balance * RATES[currency]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            status = ("RESTRUCTURED" if i <= 8 else "CLOSED" if i > 180
                      else "DELINQUENT" if i % 7 == 0 else "ACTIVE")
            booking = "2025-04-02" if i in (9, 10) else f"2025-03-{1 + i % 28:02d}"
            writer.writerow([f"L{i:04d}", f"C{client:02d}", rng.choice(["MTG", "REV", "TERM"]),
                             currency, f"{balance:.2f}", f"{usd:.2f}", status, booking])


if __name__ == "__main__":
    generate()
