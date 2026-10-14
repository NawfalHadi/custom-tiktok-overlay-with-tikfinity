import os
import csv
import time
from datetime import datetime

CSV_DIR = 'bin'
CSV_PATH = os.path.join(CSV_DIR, 'gift_streaks.csv')

def init_csv_storage():
    os.makedirs(CSV_DIR, exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['username', 'coin', 'gifted_at'])

def log_and_calculate_streak(username, diamond_count, repeat_count):
    init_csv_storage()
    current_timestamp = time.time()
    current_iso_time = datetime.now().isoformat()
    
    gift_coin_value = int(diamond_count) * int(repeat_count)
    user_rows = []

    # 1. Read existing records from CSV
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                user_rows.append(row)

    # 2. Append new event ONCE
    with open(CSV_PATH, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([username, gift_coin_value, current_iso_time])

    # Include current event in memory calculation
    user_rows.append({
        'username': username,
        'coin': str(gift_coin_value),
        'gifted_at': current_iso_time
    })

    # 3. Calculate 5-second window total
    active_streak_coins = 0
    for row in user_rows:
        if row['username'] == username:
            try:
                row_time = datetime.fromisoformat(row['gifted_at']).timestamp()
                if current_timestamp - row_time <= 5.0:
                    active_streak_coins += int(row['coin'])
            except Exception:
                pass
                
    print(f"-> [STREAK LOGGED] @{username} added {gift_coin_value} coins. 5s Window Total: {active_streak_coins} coins.")
    return active_streak_coins