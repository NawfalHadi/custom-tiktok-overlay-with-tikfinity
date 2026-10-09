import asyncio
import websockets
import json
import sqlite3
import os

def init_db():
    os.makedirs('datas', exist_ok=True)
    conn = sqlite3.connect('datas/viewers.db', timeout=10.0)
    cursor = conn.cursor()
    
    # Ensure tb_members exists
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
        # Search for viewer by uniqueId or username in tb_viewers
        search_name = unique_id or nickname
        cursor.execute('SELECT id FROM tb_viewers WHERE username = ?', (search_name,))
        viewer = cursor.fetchone()
        
        # A viewer must already exist in tb_viewers before becoming a member.
        if not viewer:
            print(f"-> [ERROR] Cannot add member: viewer '{search_name}' was not found in tb_viewers.")
            return

        viewer_id = viewer[0]

        # Insert into tb_members (or ignore if already a member)
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

async def inspect_gifts():
    init_db()
    uri = "ws://localhost:21213/"
    
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("-> [GIFT INSPECTOR] Connected to TikFinity! Monitoring membership gifts...")
                async for message in websocket:
                    try:
                        res = json.loads(message)
                        if res.get("event") == "gift":
                            gift_data = res.get("data", {})
                            gift_id = gift_data.get("giftId")
                            unique_id = gift_data.get("uniqueId")
                            nickname = gift_data.get("nickname")

                            # Check for target membership giftId (7934)
                            if gift_id == 7934:
                                print(f"\n================ MEMBERSHIP GIFT DETECTED (GiftId: {gift_id}) ================")
                                process_member_gift(unique_id, nickname)
                                print("========================================================================\n")

                    except Exception as e:
                        print(f"Error parsing gift payload: {e}")

        except Exception as e:
            print(f"-> [GIFT INSPECTOR] Connection error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

def run_gift_inspector():
    asyncio.run(inspect_gifts())

if __name__ == "__main__":
    run_gift_inspector()