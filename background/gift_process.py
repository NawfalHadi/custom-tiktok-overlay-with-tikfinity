import socketio
import requests
import sqlite3

# Initialize standard Socket.IO client
sio = socketio.Client()

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
            gift_id = gift_data.get("giftId", "")
            unique_id = gift_data.get("uniqueId") or gift_data.get("nickname") or "User"
            avatar_url = gift_data.get("profilePictureUrl") or ""
            gift_name = gift_data.get("giftName", "Special Gift")
            diamond_count = int(gift_data.get("diamondCount", 0))
            repeat_count = int(gift_data.get("repeatCount", 1))

            if gift_id == 7934:
                process_member_gift(unique_id, gift_data.get("nickname", unique_id))

            if diamond_count > 0:
                # Forward raw gift data to Flask backend endpoint
                try:
                    requests.post("http://127.0.0.1:5000/api/gift-event", json={
                        "username": unique_id,
                        "avatarUrl": avatar_url,
                        "giftName": gift_name,
                        "diamondCount": diamond_count,
                        "repeatCount": repeat_count
                    }, timeout=2.0)
                except Exception as req_err:
                    print(f"-> [HTTP ERROR] Failed to forward gift event: {req_err}")

    except Exception as e:
        print(f"Error processing socket event payload: {e}")

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


def run_gift_inspector():
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