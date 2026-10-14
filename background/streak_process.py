import os
import csv
import time
from datetime import datetime
import requests

CSV_DIR = 'bin'
CSV_PATH = os.path.join(CSV_DIR, 'gift_streaks.csv')

def init_csv_storage():
    os.makedirs(CSV_DIR, exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['username', 'coin', 'gifted_at'])

def process_gift_streak(username, avatar_url, gift_name, diamond_count, repeat_count):
    init_csv_storage()
    current_timestamp = time.time()
    current_iso_time = datetime.now().isoformat()
    
    gift_coin_value = int(diamond_count) * int(repeat_count)
    user_rows = []

    # 1. Read existing records
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                user_rows.append(row)

    # 2. Append the new gift event to the CSV file
    with open(CSV_PATH, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([username, gift_coin_value, current_iso_time])

    # Add the current incoming gift to our memory list for immediate calculation
    user_rows.append({
        'username': username,
        'coin': str(gift_coin_value),
        'gifted_at': current_iso_time
    })

    print(f"-> [CSV LOGGED] @{username} added {gift_coin_value} coins ({gift_name} x{repeat_count})")

    # 3. Calculate total coins for this user within the active 5-second window
    active_streak_coins = 0
    for row in user_rows:
        if row['username'] == username:
            try:
                row_time = datetime.fromisoformat(row['gifted_at']).timestamp()
                # Check if it happened within the last 5 seconds
                if current_timestamp - row_time <= 5.0:
                    active_streak_coins += int(row['coin'])
            except Exception as e:
                pass
    
    print(f"-> [STREAK CHECK] @{username} active streak total (last 5s): {active_streak_coins} coins.")

    # 4. Trigger Upeti if active streak hits threshold (>= 20 coins)
    if active_streak_coins >= 1:
        print(f"-> [UPETI TRIGGERED] @{username} reached {active_streak_coins} coins streak!")
        try:
            requests.post("http://127.0.0.1:5000/upetitriger", json={
                "username": username,
                "avatarUrl": avatar_url,
                "giftName": f"Streak ({active_streak_coins} Coins)",
                "giftCount": active_streak_coins,
                "giftIconUrl": ""
            }, timeout=2.0)
        except Exception as req_err:
            print(f"-> [HTTP ERROR] Failed to trigger upeti: {req_err}")