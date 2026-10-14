import socketio
import requests

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
            unique_id = gift_data.get("uniqueId") or gift_data.get("nickname") or "User"
            avatar_url = gift_data.get("profilePictureUrl") or ""
            gift_name = gift_data.get("giftName", "Special Gift")
            diamond_count = int(gift_data.get("diamondCount", 0))
            repeat_count = int(gift_data.get("repeatCount", 1))

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