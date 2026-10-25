import time
import requests


from utils.config import MEMBER_GIFT_ID, SERVER_URL
from utils.db import create_viewer, db_connection, find_viewer, find_viewer_detail
from utils.socket import create_client, run_forever
from controller.auth_controller import verify_code_from_tiktok

LABEL = "MESSAGE PROCESS"
DEFAULT_AVATAR = "https://via.placeholder.com/150"
POINTS_TRIGGER_URL = f"{SERVER_URL}/api/trigger/points"

sio = create_client(LABEL)

# Cooldown tracking: { username: timestamp }
points_cooldown = {}
COOLDOWN_DURATION = 10  # Waktu tenggang (10 seconds per user)


def join_viewer(user, profile_url):
    """Save a viewer and initialize their stats unless they already exist."""
    try:
        print(f"-> [SOCKET.IO COMMAND] Registering viewer '{user}'...")
        with db_connection() as conn:
            if find_viewer(conn, user):
                print(f"-> [!] Username '{user}' already exists in database. Ignored.")
                return
            create_viewer(conn, user, profile_url)
        print(f"-> [SUCCESS] Saved new viewer from Socket.IO event: '{user}'")
    except Exception as error:
        print(f"-> [DATABASE ERROR] {error}")


def handle_points_command(user, profile_url):
    current_time = time.time()
    
    # 1. Waktu Tenggang (Cooldown) Check
    if user in points_cooldown:
        elapsed = current_time - points_cooldown[user]
        if elapsed < COOLDOWN_DURATION:
            remaining = int(COOLDOWN_DURATION - elapsed)
            print(f"-> [POINTS COOLDOWN] @{user} must wait {remaining}s before checking points again.")
            return

    # Update cooldown timestamp
    points_cooldown[user] = current_time

    # 2. Fetch viewer points and profile picture using db.py
    points = 0
    avatar = profile_url
    try:
        with db_connection() as conn:
            row = find_viewer_detail(conn, user)
            if row:
                # row schema: (id, username, profile_picture_url, points)
                avatar = row[2] or profile_url
                points = row[3] if row[3] is not None else 0
    except Exception as error:
        print(f"-> [DATABASE ERROR] Failed to get points for '{user}': {error}")

    print(f"-> [POINTS CHECK SUCCESS] @{user} has {points} points. Triggering banner.")

    try:
        requests.post(
            POINTS_TRIGGER_URL,
            json={
                "username": user,
                "points": points,
                "avatarUrl": avatar,
            },
            timeout=2.0,
        )
    except requests.RequestException as error:
        print(f"-> [POINTS HTTP ERROR] {error}")


@sio.on("tiktok_event")
def on_tiktok_event(res):
    if not res:
        return

    event = res.get("event")
    data = res.get("data") or {}
    profile_url = data.get("profilePictureUrl", DEFAULT_AVATAR)
    user = data.get("uniqueId") or data.get("nickname") or "User"

    if event == "chat":
        msg = data.get("comment", "")
        print(f"-> [SOCKET.IO CHAT] {user}: {msg}")

        if "!join" in msg.lower():
            join_viewer(user, profile_url)

        if msg.strip().startswith("!verify"):
            parts = msg.strip().split()
            if len(parts) >= 2:
                print(f"-> [VERIFY COMMAND] Dari @{user}: {msg}")
                verify_code_from_tiktok(user, parts[1])

        if msg.strip().startswith("!points") or msg.strip().startswith("!poin"):
            print(f"-> [POINTS COMMAND] Dari @{user}: {msg}")
            handle_points_command(user, profile_url)

    elif event == "follow":
        if data.get("uniqueId"):
            print(f"-> [SOCKET.IO FOLLOW] '{user}' followed.")
            join_viewer(user, profile_url)

    elif event == "gift":
        gift_id = data.get("giftId")
        if gift_id == MEMBER_GIFT_ID:
            print(f"-> [SOCKET.IO GIFT] '{user}' sent gift ID {gift_id}.")
            join_viewer(user, profile_url)

    elif event == "member":
        if data.get("uniqueId"):
            print(f"-> [SOCKET.IO MEMBER] '{user}' joined the stream.")


def run_message_process():
    run_forever(sio, LABEL)


if __name__ == "__main__":
    run_message_process()