import socketio
import sqlite3
from pathlib import Path
import subprocess
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'datas' / 'viewers.db'
DB_INIT_PATH = BASE_DIR / 'datas' / 'init.py'

# Inisialisasi Socket.IO Client
sio = socketio.Client()

def init_db():
    if not DB_PATH.exists():
        subprocess.run([sys.executable, str(DB_INIT_PATH)], check=True)

# Mendengarkan event 'tiktok_event' yang dikirim oleh server Flask-SocketIO
@sio.on('tiktok_event')
def on_tiktok_event(res):
    if res and res.get("event") == "chat":
        d = res.get("data") or {}
        
        user = d.get("uniqueId") or d.get("nickname") or "User"
        msg = d.get("comment", "")
        

        print(f"-> [SOCKET.IO CHAT] {user}: {msg}")
        
        # Filter command !join
        if "!join" in msg.lower():
            init_db()
            conn = sqlite3.connect(DB_PATH, timeout=10.0)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM tb_viewers WHERE username = ?', (user,))
            existing = cursor.fetchone()
            
            if existing:
                print(f"-> [!] Username '{user}' already exists in database. Ignored.")
            else:
                cursor.execute('INSERT INTO tb_viewers (username) VALUES (?)', (user,))
                conn.commit()
                print(f"-> [SUCCESS] Saved new viewer from Socket.IO event: '{user}'")
                
            conn.close()

@sio.event
def connect():
    print("-> [MESSAGE PROCESS] Connected to Flask-SocketIO Server (http://127.0.0.1:5000)!")

@sio.event
def disconnect():
    print("-> [MESSAGE PROCESS] Disconnected from Flask-SocketIO Server.")

def run_message_process():
    try:
        # Connect ke server Flask-SocketIO kamu (bukan ke ws TikFinity)
        sio.connect('http://127.0.0.1:5000')
        sio.wait()
    except Exception as e:
        print(f"-> [SOCKET.IO CLIENT ERROR] Connection failed: {e}")

if __name__ == "__main__":
    run_message_process()