import csv
from datetime import datetime


def write_log(desk_id, state, elapsed_seconds, path="logs.csv"):
    with open(path, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            desk_id,
            state,
            int(elapsed_seconds)
        ])