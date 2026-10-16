import socketio
import sqlite3
from pathlib import Path

from controller.auth_controller import verify_code_from_tiktok

# Correct base directory: point to project root instead of background/
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'datas' / 'viewers.db'

# Inisialisasi Socket.IO Client
sio = socketio.Client()


def join_viewer(user, profile_url):
    """Save a viewer and initialize their stats unless they already exist."""
    try:
        print(f"-> [SOCKET.IO COMMAND] Registering viewer '{user}'...")
        with sqlite3.connect(DB_PATH, timeout=10.0) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM tb_viewers WHERE username = ?', (user,))
            if cursor.fetchone():
                print(f"-> [!] Username '{user}' already exists in database. Ignored.")
                return

            cursor.execute(
                'INSERT INTO tb_viewers (username, profile_picture_url) VALUES (?, ?)',
                (user, profile_url),
            )
            viewer_id = cursor.lastrowid
            cursor.execute(
                'INSERT INTO tb_stats (id_viewer, points) VALUES (?, ?)',
                (viewer_id, 0),
            )
        print(f"-> [SUCCESS] Saved new viewer from Socket.IO event: '{user}'")
    except Exception as e:
        print(f"-> [DATABASE ERROR] {e}")


# Mendengarkan event 'tiktok_event' yang dikirim oleh server Flask-SocketIO
@sio.on('tiktok_event')
def on_tiktok_event(res):
    if not res:
        return

    event = res.get("event")
    d = res.get("data") or {}
    profile_url = d.get("profilePictureUrl", "https://via.placeholder.com/150")

    if event == "chat":
        user = d.get("uniqueId") or d.get("nickname") or "User"
        msg = d.get("comment", "")
        print(f"-> [SOCKET.IO CHAT] {user}: {msg}")
        
        # 1. Handle command !join
        if "!join" in msg.lower():
            join_viewer(user, profile_url)
            
        # 2. Handle command !verify <code_number>
        if msg.strip().startswith("!verify"):
            parts = msg.strip().split()
            if len(parts) >= 2:
                code_input = parts[1]
                print(f"-> [VERIFY COMMAND] Dari @{user}: {msg}")
                verify_code_from_tiktok(user, code_input)

    elif event == "follow":
        follower = d.get("uniqueId")
        if follower:
            print(f"-> [SOCKET.IO FOLLOW] '{follower}' followed.")
            join_viewer(follower, profile_url)

    elif event == "gift":
        giftId = d.get("giftId")
        user = d.get("uniqueId") or d.get("nickname") or "User"
        if giftId == 7934:
            print(f"-> [SOCKET.IO GIFT] '{user}' sent gift ID {giftId}.")
            join_viewer(user, profile_url)
            
    elif event == "member":
        member = d.get("uniqueId")
        if member:
            print(f"-> [SOCKET.IO MEMBER] '{member}' join the stream.")

@sio.event
def connect():
    print("-> [MESSAGE PROCESS] Connected to Flask-SocketIO Server (http://127.0.0.1:5000)!")

@sio.event
def disconnect():
    print("-> [MESSAGE PROCESS] Disconnected from Flask-SocketIO Server.")

def run_message_process():
    try:
        sio.connect('http://127.0.0.1:5000')
        sio.wait()
    except Exception as e:
        print(f"-> [SOCKET.IO CLIENT ERROR] Connection failed: {e}")

if __name__ == "__main__":
    run_message_process()