import socketio
import sqlite3
from pathlib import Path

# Correct base directory: point to project root instead of background/
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'datas' / 'viewers.db'

# Inisialisasi Socket.IO Client
sio = socketio.Client()

# Mendengarkan event 'tiktok_event' yang dikirim oleh server Flask-SocketIO
@sio.on('tiktok_event')
def on_tiktok_event(res):
    if res and res.get("event") == "chat":
        d = res.get("data") or {}
        
        user = d.get("uniqueId") or d.get("nickname") or "User"
        msg = d.get("comment", "")
        profileUrl = d.get("profilePictureUrl", "https://via.placeholder.com/150")
        
        print(f"-> [SOCKET.IO CHAT] {user}: {msg}")
        
        # Filter command !join
        if "!join" in msg.lower():
            try:
                print(f"-> [SOCKET.IO COMMAND] '!join' command detected from user '{user}'. Attempting to save to database...")
                conn = sqlite3.connect(DB_PATH, timeout=10.0)
                cursor = conn.cursor()
                
                # Check if username already exists
                cursor.execute('SELECT id FROM tb_viewers WHERE username = ?', (user,))
                existing = cursor.fetchone()
                
                if existing:
                    print(f"-> [!] Username '{user}' already exists in database. Ignored.")
                else:
                    cursor.execute(
                        'INSERT INTO tb_viewers (username, profile_picture_url) VALUES (?, ?)',
                        (user, profileUrl),
                    )
                    viewer_id = cursor.lastrowid
                    cursor.execute(
                        'INSERT INTO tb_stats (id_viewer, points) VALUES (?, ?)',
                        (viewer_id, 0),
                    )
                    conn.commit()
                    print(f"-> [SUCCESS] Saved new viewer from Socket.IO event: '{user}'")
                    
                conn.close()
            except Exception as e:
                print(f"-> [DATABASE ERROR] {e}")

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