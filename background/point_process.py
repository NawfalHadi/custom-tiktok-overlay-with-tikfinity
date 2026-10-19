import sqlite3
import time
from pathlib import Path
from datetime import datetime
import threading
import socketio

sio = socketio.Client()
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "datas" / "viewers.db"

COIN_TO_POINT_MULTIPLIER = 100
MEMBER_POINT_MULTIPLIER = 1.2

# Konfigurasi Anti-Spam Chat
CHAT_POINT_REWARD = 50       
COOLDOWN_SECONDS = 30.0      
MIN_MESSAGE_LENGTH = 3       

# Konfigurasi Daily Check-in
DAILY_POINT_REWARD = 10000     

# Konfigurasi Watch Time (Poin Pasif)
WATCH_TIME_INTERVAL = 300    # Cek setiap 5 menit (300 detik)
WATCH_TIME_REWARD = 20       # Poin yang didapat per interval
ACTIVITY_TIMEOUT = 900       # Dianggap masih menonton jika aktif dalam 15 menit terakhir (900 detik)

# Cache & Threading Lock
last_chat_times = {}
active_viewers = {}  # Format: { "username": timestamp_aktivitas_terakhir }
viewer_lock = threading.Lock()

def award_points(username, coin_value, gift_multiplier=1):
    with sqlite3.connect(DB_PATH) as connection:
        viewer = connection.execute(
            """
            SELECT v.id, EXISTS(
                SELECT 1 FROM tb_members AS m WHERE m.id_viewer = v.id
            )
            FROM tb_viewers AS v
            WHERE LOWER(v.username) = LOWER(?)
            """,
            (username,),
        ).fetchone()

        if viewer is None:
            return

        multiplier = (MEMBER_POINT_MULTIPLIER if viewer[1] else 1) * gift_multiplier
        points = int(coin_value * COIN_TO_POINT_MULTIPLIER * multiplier)
        connection.execute(
            """
            INSERT INTO tb_stats (id_viewer, points) VALUES (?, ?)
            ON CONFLICT(id_viewer) DO UPDATE SET points = points + excluded.points
            """,
            (viewer[0], points),
        )

def award_chat_points(username):
    global last_chat_times
    current_time = time.time()
    
    if username in last_chat_times:
        if current_time - last_chat_times[username] < COOLDOWN_SECONDS:
            return False

    last_chat_times[username] = current_time

    with sqlite3.connect(DB_PATH) as connection:
        viewer = connection.execute(
            """
            SELECT v.id, EXISTS(
                SELECT 1 FROM tb_members AS m WHERE m.id_viewer = v.id
            )
            FROM tb_viewers AS v
            WHERE LOWER(v.username) = LOWER(?)
            """,
            (username,),
        ).fetchone()

        if viewer is None:
            return False

        multiplier = MEMBER_POINT_MULTIPLIER if viewer[1] else 1.0
        points = int(CHAT_POINT_REWARD * multiplier)

        connection.execute(
            """
            INSERT INTO tb_stats (id_viewer, points) VALUES (?, ?)
            ON CONFLICT(id_viewer) DO UPDATE SET points = points + excluded.points
            """,
            (viewer[0], points),
        )
    return True

def handle_daily_checkin(username):
    today = datetime.now().strftime('%Y-%m-%d')
    with sqlite3.connect(DB_PATH) as connection:
        viewer = connection.execute(
            """
            SELECT v.id, v.last_daily_claim, EXISTS(
                SELECT 1 FROM tb_members AS m WHERE m.id_viewer = v.id
            )
            FROM tb_viewers AS v
            WHERE LOWER(v.username) = LOWER(?)
            """,
            (username,),
        ).fetchone()

        if viewer is None:
            return

        viewer_id, last_claim, is_member = viewer[0], viewer[1], viewer[2]

        if last_claim == today:
            return

        multiplier = MEMBER_POINT_MULTIPLIER if is_member else 1.0
        points = int(DAILY_POINT_REWARD * multiplier)

        connection.execute(
            "UPDATE tb_viewers SET last_daily_claim = ? WHERE id = ?",
            (today, viewer_id)
        )
        connection.execute(
            """
            INSERT INTO tb_stats (id_viewer, points) VALUES (?, ?)
            ON CONFLICT(id_viewer) DO UPDATE SET points = points + excluded.points
            """,
            (viewer_id, points),
        )
        print(f"-> [DAILY CHECK-IN] @{username} mendapat {points} poin absen.")

def record_activity(username):
    """Mencatat atau memperbarui waktu aktivitas terakhir penonton."""
    with viewer_lock:
        active_viewers[username] = time.time()

def watch_time_background_worker():
    """Background thread yang membagikan poin pasif secara berkala kepada penonton aktif."""
    while True:
        time.sleep(WATCH_TIME_INTERVAL)
        current_time = time.time()
        
        with viewer_lock:
            # Ambil salinan user yang aktif dalam batas waktu timeout
            eligible_users = [
                user for user, last_seen in active_viewers.items()
                if current_time - last_seen <= ACTIVITY_TIMEOUT
            ]

        if not eligible_users:
            continue

        print(f"-> [WATCH TIME] Membagikan poin pasif ke {len(eligible_users)} penonton aktif...")

        with sqlite3.connect(DB_PATH) as connection:
            for username in eligible_users:
                try:
                    viewer = connection.execute(
                        """
                        SELECT v.id, EXISTS(
                            SELECT 1 FROM tb_members AS m WHERE m.id_viewer = v.id
                        )
                        FROM tb_viewers AS v
                        WHERE LOWER(v.username) = LOWER(?)
                        """,
                        (username,),
                    ).fetchone()

                    if viewer:
                        viewer_id, is_member = viewer[0], viewer[1]
                        multiplier = MEMBER_POINT_MULTIPLIER if is_member else 1.0
                        points = int(WATCH_TIME_REWARD * multiplier)

                        connection.execute(
                            """
                            INSERT INTO tb_stats (id_viewer, points) VALUES (?, ?)
                            ON CONFLICT(id_viewer) DO UPDATE SET points = points + excluded.points
                            """,
                            (viewer_id, points),
                        )
                except Exception as e:
                    print(f"-> [WATCH TIME ERROR] Gagal memberi poin ke @{username}: {e}")
            connection.commit()
        print("-> [WATCH TIME] Poin pasif berhasil dibagikan.")

@sio.on("connect")
def on_connect():
    print("-> [POINT PROCESSOR] Connected to Flask Socket.IO server!")

@sio.on("disconnect")
def on_disconnect():
    print("-> [POINT PROCESSOR] Disconnected from server.")

@sio.on("tiktok_event")
def handle_tiktok_event(res):
    try:
        event_type = res.get("event")
        data = res.get("data", {})
        username = data.get("uniqueId") or data.get("nickname") or "User"

        # Setiap ada event apa pun dari user, catat aktivitasnya untuk watch time
        if username and username != "User":
            record_activity(username)

        # 1. Handle Gift Events[cite: 14]
        if event_type == "gift":
            diamond_count = int(data.get("diamondCount", 0))
            coin_value = diamond_count
            
            if coin_value < 5:
                output = "small gift"
                gift_multiplier = 1
            elif coin_value < 20:
                output = "medium gift"
                gift_multiplier = 1.15
            elif coin_value < 50:
                output = "large gift"
                gift_multiplier = 1.2
            else:
                output = "special gift"
                gift_multiplier = 1.4

            award_points(username, coin_value, gift_multiplier)
            print(f"-> [POINT PROCESSOR] {username} sent a {output} ({coin_value} coins)[cite: 14]")

        # 2. Handle Chat Events
        elif event_type in ["chat", "comment"]:
            message = data.get("comment") or data.get("message") or ""
            msg_clean = message.strip().lower()

            if msg_clean in ["!daily", "!absen"]:
                handle_daily_checkin(username)
            elif msg_clean.startswith("!"):
                return
            else:
                if len(message.strip()) >= MIN_MESSAGE_LENGTH:
                    success = award_chat_points(username)
                    if success:
                        print(f"-> [CHAT POINT] @{username} mendapat poin aktif chat.")

        # 3. Handle Follow / Member Events (Mencatat kehadiran)
        elif event_type in ["follow", "member"]:
            print(f"-> [STREAM EVENT] @{username} melakukan {event_type}.")

    except (TypeError, ValueError) as error:
        print(f"-> [POINT PROCESSOR] Invalid value: {error}")
    except Exception as error:
        print(f"-> [POINT PROCESSOR] Failed to process event: {error}")

def run_point_inspector():
    # Jalankan background worker untuk watch time di thread terpisah
    watch_thread = threading.Thread(target=watch_time_background_worker, daemon=True)
    watch_thread.start()
    print("-> [WATCH TIME WORKER] Background thread aktif.")

    while True:
        try:
            print("-> [POINT PROCESSOR] Connecting to Flask server on port 5000...")
            sio.connect("http://127.0.0.1:5000", transports=["polling"])
            sio.wait()
        except Exception as error:
            print(
                f"-> [POINT PROCESSOR] Connection error: {error}. "
                "Reconnecting in 5s..."
            )
            time.sleep(5)

if __name__ == "__main__":
    run_point_inspector()