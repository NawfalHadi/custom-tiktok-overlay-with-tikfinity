import socketio
import sqlite3
import os
import requests

from .streak_process import process_gift_streak

# Initialize standard Socket.IO client
sio = socketio.Client()

def init_db():
    os.makedirs('datas', exist_ok=True)
    conn = sqlite3.connect('datas/viewers.db', timeout=10.0)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tb_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_viewer INTEGER NOT NULL UNIQUE,
            is_announced INTEGER NOT NULL DEFAULT 0 CHECK (is_announced IN (0, 1)),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            joined_at TEXT,
            FOREIGN KEY (id_viewer) REFERENCES tb_viewers(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

def process_member_gift(unique_id, nickname):
    conn = sqlite3.connect('datas/viewers.db', timeout=10.0)
    cursor = conn.cursor()
    
    try:
        search_name = unique_id or nickname
        cursor.execute('SELECT id FROM tb_viewers WHERE username = ?', (search_name,))
        viewer = cursor.fetchone()
        
        if not viewer:
            print(f"-> [ERROR] Cannot add member: viewer '{search_name}' was not found in tb_viewers.")
            return

        viewer_id = viewer[0]

        cursor.execute('''
            INSERT OR IGNORE INTO tb_members (id_viewer, joined_at)
            VALUES (?, CURRENT_TIMESTAMP)
        ''', (viewer_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"-> [NEW MEMBER] User '{search_name}' (Viewer ID: {viewer_id}) successfully added to tb_members!")
        else:
            print(f"-> [INFO] User '{search_name}' is already in tb_members.")

    except Exception as e:
        print(f"-> [DATABASE ERROR] Failed to add member: {e}")
    finally:
        conn.close()

# Listen to incoming events via Socket.IO (@sio.on)
@sio.on('connect')
def on_connect():
    print("-> [GIFT PROCESSOR] Connected to Flask Socket.IO server!")

@sio.on('disconnect')
def on_disconnect():
    print("-> [GIFT PROCESSOR] Disconnected from server.")

@sio.on('tiktok_event')
def handle_tiktok_event(res):
    try:
        if res.get("event") == "gift":
            gift_data = res.get("data", {})
            
            gift_id = gift_data.get("giftId")
            unique_id = gift_data.get("uniqueId") or gift_data.get("nickname") or "User"
            nickname = gift_data.get("nickname")
            avatar_url = gift_data.get("profilePictureUrl") or ""
            gift_name = gift_data.get("giftName", "Special Gift")
            diamond_count = int(gift_data.get("diamondCount", 0))
            repeat_count = int(gift_data.get("repeatCount", 1))

            # 1. Check for target membership giftId (7934)
            if gift_id == 7934:
                print(f"\n================ MEMBERSHIP GIFT DETECTED (GiftId: {gift_id}) ================")
                process_member_gift(unique_id, nickname)
                print("========================================================================\n")

            # 2. Delegate to streak_process for CSV tracking and 5-second window accumulation
            if diamond_count > 0:
                process_gift_streak(unique_id, avatar_url, gift_name, diamond_count, repeat_count)

    except Exception as e:
        print(f"Error processing socket event payload: {e}")

def run_gift_inspector():
    init_db()
    while True:
        try:
            print("-> [GIFT PROCESSOR] Attempting to connect to Flask server on port 5000...")
            sio.connect('http://127.0.0.1:5000', transports=['polling'])
            sio.wait()
        except Exception as e:
            print(f"-> [GIFT PROCESSOR] Connection error: {e}. Reconnecting in 5s...")
            import time
            time.sleep(5)

if __name__ == "__main__":
    run_gift_inspector()