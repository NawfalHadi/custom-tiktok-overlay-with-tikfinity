import csv
import time
from datetime import datetime

from utills.config import BASE_DIR

CSV_DIR = BASE_DIR / "bin"
CSV_PATH = CSV_DIR / "gift_streaks.csv"
CSV_HEADER = ["username", "coin", "gifted_at"]
STREAK_WINDOW = 5.0  # seconds


def init_csv_storage():
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(CSV_HEADER)


def log_and_calculate_streak(username, diamond_count, repeat_count):
    init_csv_storage()
    now_ts = time.time()
    now_iso = datetime.now().isoformat()
    coin_value = int(diamond_count) * int(repeat_count)

    with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([username, coin_value, now_iso])

    active_streak_coins = 0
    with open(CSV_PATH, mode="r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["username"] != username:
                continue
            try:
                row_ts = datetime.fromisoformat(row["gifted_at"]).timestamp()
                if now_ts - row_ts <= STREAK_WINDOW:
                    active_streak_coins += int(row["coin"])
            except (KeyError, ValueError):
                continue

    print(f"-> [STREAK LOGGED] @{username} added {coin_value} coins. "
          f"5s Window Total: {active_streak_coins} coins.")
    return active_streak_coins