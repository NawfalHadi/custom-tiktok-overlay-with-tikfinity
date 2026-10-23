import threading
import time
from datetime import datetime

from utills.config import (
    ACTIVITY_TIMEOUT,
    CHAT_POINT_REWARD,
    COIN_TO_POINT_MULTIPLIER,
    COOLDOWN_SECONDS,
    DAILY_POINT_REWARD,
    MIN_MESSAGE_LENGTH,
    WATCH_TIME_INTERVAL,
    WATCH_TIME_REWARD,
)
from utills.db import (
    add_points,
    db_connection,
    find_viewer,
    member_multiplier,
)
from utills.socket import create_client, run_forever

LABEL = "POINT PROCESSOR"

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


def award_points(username, coin_value, gift_multiplier=1.0):
    with db_connection() as conn:
        viewer = find_viewer(conn, username)
        if viewer is None:
            return

        viewer_id, _, is_member = viewer
        points = int(coin_value * COIN_TO_POINT_MULTIPLIER
                     * member_multiplier(is_member) * gift_multiplier)
        add_points(conn, viewer_id, points)


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
        add_points(conn, viewer_id, int(CHAT_POINT_REWARD * member_multiplier(is_member)))
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
                        add_points(conn, viewer_id,
                                   int(WATCH_TIME_REWARD * member_multiplier(is_member)))
                except Exception as error:
                    print(f"-> [WATCH TIME ERROR] Gagal memberi poin ke @{username}: {error}")
        print("-> [WATCH TIME] Poin pasif berhasil dibagikan.")


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
    print("-> [WATCH TIME WORKER] Background thread aktif.")
    run_forever(sio, LABEL)


if __name__ == "__main__":
    run_point_inspector()