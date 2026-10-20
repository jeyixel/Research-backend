import csv
import shutil
from pathlib import Path

path = Path("data/candidates.csv")
shutil.copy2(path, path.with_suffix(".csv.bak"))

# after running discover use this if you want to approve all candidates for training

with path.open("r", newline="", encoding="utf-8-sig") as source:
    reader = csv.DictReader(source)
    rows = list(reader)
    columns = reader.fieldnames

for row in rows:
    row["approve"] = "y"

with path.open("w", newline="", encoding="utf-8") as destination:
    writer = csv.DictWriter(destination, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

print(f"Approved {len(rows)} channels. Backup saved as {path.with_suffix('.csv.bak')}.")