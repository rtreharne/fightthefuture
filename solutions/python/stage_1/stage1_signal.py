import csv
import sys

if len(sys.argv) < 2:
    raise SystemExit("Usage: python stage1_signal.py <dataset_path>")

dataset_path = sys.argv[1]
with open(dataset_path, newline="") as handle:
    rows = list(csv.DictReader(handle))

signals = sorted(
    (row for row in rows if int(row["keep"]) == 1),
    key=lambda row: int(row["pos"]),
)

digits = []
for row in signals:
    encoded = int(row["encoded"])
    key = int(row["key"])
    pos = int(row["pos"])
    digit = (encoded - key - (pos * 3)) % 10
    digits.append(str(digit))

print("".join(digits))