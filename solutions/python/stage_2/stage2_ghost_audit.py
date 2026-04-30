import csv
import sys


if len(sys.argv) < 2:
    raise SystemExit("Usage: python stage2_ghost_audit.py <dataset_path>")


dataset_path = sys.argv[1]

with open(dataset_path, newline="") as handle:
    rows = list(csv.DictReader(handle))

if not rows:
    raise SystemExit("Dataset is empty")

bias_key = int(rows[0]["bias_key"])

total = 0
for row in rows:
    if (
        row["status"] == "ACTIVE"
        and int(row["authentic"]) == 1
        and int(row["priority"]) >= 4
    ):
        units = int(row["units"])
        multiplier = int(row["multiplier"])
        total += units * multiplier

code = (total + bias_key) % 1_000_000
print(f"{code:06d}")
