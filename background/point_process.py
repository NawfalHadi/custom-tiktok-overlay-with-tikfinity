import threading
import time
import csv
from pathlib import Path
from datetime import datetime

from utils.extensions import socketio

from controller.points_controlller import get_leaderboards
from utils.config import (
    ACTIVITY_TIMEOUT,
    CHAT_POINT_REWARD,
    COIN_TO_POINT_MULTIPLIER,
    COOLDOWN_SECONDS,
    DAILY_POINT_REWARD,
    MIN_MESSAGE_LENGTH,
    WATCH_TIME_INTERVAL,
    WATCH_TIME_REWARD,
    LEADERBOARD_INTERVAL,
)
from utils.db import (
    add_points,
    db_connection,
    find_viewer,
    member_multiplier,
)
from utils.socket import create_client, run_forever

LABEL = "POINT PROCESSOR"
BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
BIN_DIR.mkdir(exist_ok=True)

daily_lock = threading.Lock()
daily_points = {}        # { "username": points earned today }
daily_file_date = None 

sio = create_client(LABEL)

last_chat_times = {}
active_viewers = {}  # { "username": last_activity_timestamp }
viewer_lock = threading.Lock()


def gift_tier(coin_value):
    """Return (label, gift multiplier) for a gift's coin value."""
    if coin_value < 5:
        return "small gift", 1.0
    if coin_value < 20:
        return "medium gift", 1.15
    if coin_value < 50:
        return "large gift", 1.2
    return "special gift", 1.4

def record_daily_points(username, points):
    """Add points to today's tally and rewrite the day's CSV."""
    global daily_points, daily_file_date
    if points <= 0:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    path = BIN_DIR / f"prajurit_points_daily_{today}.csv"

    with daily_lock:
        # New day (or first run): load the existing file so restarts don't lose counts
        if daily_file_date != today:
            daily_points = {}
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        daily_points[row["username"]] = int(row["points_today"])
            daily_file_date = today

        daily_points[username] = daily_points.get(username, 0) + points

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "points_today"])
            for user, pts in sorted(daily_points.items(), key=lambda x: x[1], reverse=True):
                writer.writerow([user, pts])

def award_points(username, coin_value, gift_multiplier=1.0):
    with db_connection() as conn:
        viewer = find_viewer(conn, username)
        if viewer is None:
            return

        viewer_id, _, is_member = viewer
        points = int(coin_value * COIN_TO_POINT_MULTIPLIER
                     * member_multiplier(is_member) * gift_multiplier)
        
        add_points(conn, viewer_id, points)
        record_daily_points(username, points)

def award_chat_points(username):
    now = time.time()
    last = last_chat_times.get(username)
    if last is not None and now - last < COOLDOWN_SECONDS:
        return False
    last_chat_times[username] = now

    with db_connection() as conn:
        viewer = find_viewer(conn, username)
        if viewer is None:
            return False

        viewer_id, _, is_member = viewer
        points = int(CHAT_POINT_REWARD * member_multiplier(is_member))
        add_points(conn, viewer_id, points)
        record_daily_points(username, points)
    return True

def handle_daily_checkin(username):
    today = datetime.now().strftime("%Y-%m-%d")
    with db_connection() as conn:
        viewer = find_viewer(conn, username)
        if viewer is None:
            return

        viewer_id, last_claim, is_member = viewer
        if last_claim == today:
            return

        points = int(DAILY_POINT_REWARD * member_multiplier(is_member))
        conn.execute(
            "UPDATE tb_viewers SET last_daily_claim = ? WHERE id = ?",
            (today, viewer_id),
        )
        add_points(conn, viewer_id, points)
        record_daily_points(username, points)
    print(f"-> [DAILY CHECK-IN] @{username} mendapat {points} poin absen.")

def record_activity(username):
    with viewer_lock:
        active_viewers[username] = time.time()

def watch_time_worker():
    """Periodically award passive points to recently active viewers."""
    while True:
        time.sleep(WATCH_TIME_INTERVAL)
        now = time.time()

        with viewer_lock:
            eligible = [
                user for user, last_seen in active_viewers.items()
                if now - last_seen <= ACTIVITY_TIMEOUT
            ]
        if not eligible:
            continue

        print(f"-> [WATCH TIME] Membagikan poin pasif ke {len(eligible)} penonton aktif...")
        with db_connection() as conn:
            for username in eligible:
                try:
                    viewer = find_viewer(conn, username)
                    if viewer:
                        viewer_id, _, is_member = viewer
                        points = int(WATCH_TIME_REWARD * member_multiplier(is_member))
                        add_points(conn, viewer_id, points)
                        record_daily_points(username, points)
                except Exception as error:
                    print(f"-> [WATCH TIME ERROR] Gagal memberi poin ke @{username}: {error}")
        print("-> [WATCH TIME] Poin pasif berhasil dibagikan.")

def leaderboard_worker():
    """Every 2 minutes, build both leaderboards and push them to the overlay."""
    while True:
        time.sleep(LEADERBOARD_INTERVAL)
        try:
            socketio.emit("leaderboard_update", get_leaderboards())
        except Exception as error:
            print(f"-> [LEADERBOARD ERROR] {error}")

@sio.on("tiktok_event")
def handle_tiktok_event(res):
    try:
        event_type = res.get("event")
        data = res.get("data") or {}
        username = data.get("uniqueId") or data.get("nickname") or "User"

        if username != "User":
            record_activity(username)

        if event_type == "gift":
            coin_value = int(data.get("diamondCount", 0))
            label, gift_multiplier = gift_tier(coin_value)
            award_points(username, coin_value, gift_multiplier)
            print(f"-> [POINT PROCESSOR] {username} sent a {label} ({coin_value} coins)")

        elif event_type in ("chat", "comment"):
            message = data.get("comment") or data.get("message") or ""
            msg_clean = message.strip().lower()

            if msg_clean in ("!daily", "!absen"):
                handle_daily_checkin(username)
            elif msg_clean.startswith("!"):
                pass  # other commands earn no points
            elif len(message.strip()) >= MIN_MESSAGE_LENGTH:
                if award_chat_points(username):
                    print(f"-> [CHAT POINT] @{username} mendapat poin aktif chat.")

        elif event_type in ("follow", "member"):
            print(f"-> [STREAM EVENT] @{username} melakukan {event_type}.")

    except (TypeError, ValueError) as error:
        print(f"-> [POINT PROCESSOR] Invalid value: {error}")
    except Exception as error:
        print(f"-> [POINT PROCESSOR] Failed to process event: {error}")

def run_point_inspector():
    threading.Thread(target=watch_time_worker, daemon=True).start()
    threading.Thread(target=leaderboard_worker, daemon=True).start()
    print("-> [WATCH TIME WORKER] Background thread aktif.")
    run_forever(sio, LABEL)


if __name__ == "__main__":
    run_point_inspector()