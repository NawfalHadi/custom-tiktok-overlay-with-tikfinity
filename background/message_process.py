import asyncio
import websockets
import json
import sqlite3
from pathlib import Path
import subprocess
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'datas' / 'viewers.db'
DB_INIT_PATH = BASE_DIR / 'datas' / 'init.py'

def init_db():
    if not DB_PATH.exists():
        subprocess.run([sys.executable, str(DB_INIT_PATH)], check=True)

async def process_messages():
    init_db()
    uri = "ws://localhost:21213/"
    
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to TikFinity! Listening for comments...")
                async for message in websocket:
                    try:
                        res = json.loads(message)
                        if res.get("event") == "chat" or res.get("event") == "comment":
                            d = res.get("data", {})
                            user = d.get("uniqueId") or "User"
                            msg = d.get("comment", "")
                            
                            print(f"{user}: {msg}")
                            
                            # Filter for '!join' in the message
                            if "!join" in msg.lower():
                                conn = sqlite3.connect(DB_PATH)
                                cursor = conn.cursor()
                                
                                # Check if username already exists
                                cursor.execute('SELECT id FROM tb_viewers WHERE username = ?', (user,))
                                existing = cursor.fetchone()
                                
                                if existing:
                                    print(f"-> [!] Username '{user}' already exists in database. Ignored.")
                                else:
                                    # Insert username into database (ignoring email)
                                    cursor.execute('INSERT INTO tb_viewers (username) VALUES (?)', (user,))
                                    conn.commit()
                                    print(f"-> [SUCCESS] Saved new viewer to datas/viewer.db: '{user}'")
                                    
                                conn.close()
                                
                    except Exception as e:
                        print(f"Error parsing message: {e}")
        except Exception as e:
            print(f"Connection error: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

def run_message_process():
    asyncio.run(process_messages())

if __name__ == "__main__":
    run_message_process()