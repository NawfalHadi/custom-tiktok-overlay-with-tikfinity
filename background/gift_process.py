import requests

from utills.config import MEMBER_GIFT_ID, SERVER_URL
from utills.db_process import add_member, db_connection, find_viewer
from utills.socket_process import create_client, run_forever

LABEL = "GIFT PROCESSOR"
GIFT_EVENT_URL = f"{SERVER_URL}/api/gift-event"

sio = create_client(LABEL)


def process_member_gift(username):
    try:
        with db_connection() as conn:
            viewer = find_viewer(conn, username)
            if not viewer:
                print(f"-> [ERROR] Cannot add member: viewer '{username}' was not found.")
                return

            viewer_id = viewer[0]
            if add_member(conn, viewer_id):
                print(f"-> [NEW MEMBER] '{username}' (Viewer ID: {viewer_id}) added to tb_members!")
            else:
                print(f"-> [INFO] '{username}' is already in tb_members.")
    except Exception as error:
        print(f"-> [DATABASE ERROR] Failed to add member: {error}")


@sio.on("tiktok_event")
def handle_tiktok_event(res):
    try:
        if res.get("event") != "gift":
            return

        data = res.get("data") or {}
        username = data.get("uniqueId") or data.get("nickname") or "User"
        diamond_count = int(data.get("diamondCount", 0))
        repeat_count = int(data.get("repeatCount", 1))

        if data.get("giftId") == MEMBER_GIFT_ID:
            process_member_gift(username)

        if diamond_count > 0:
            try:
                requests.post(GIFT_EVENT_URL, json={
                    "username": username,
                    "avatarUrl": data.get("profilePictureUrl") or "",
                    "giftName": data.get("giftName", "Special Gift"),
                    "diamondCount": diamond_count,
                    "repeatCount": repeat_count,
                }, timeout=2.0)
            except requests.RequestException as error:
                print(f"-> [HTTP ERROR] Failed to forward gift event: {error}")

    except (TypeError, ValueError) as error:
        print(f"-> [{LABEL}] Invalid gift payload: {error}")


def run_gift_inspector():
    run_forever(sio, LABEL)


if __name__ == "__main__":
    run_gift_inspector()