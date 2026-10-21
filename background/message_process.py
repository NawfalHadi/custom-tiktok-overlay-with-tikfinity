from background.helper.config import MEMBER_GIFT_ID
from background.helper.db_process import create_viewer, db_connection, find_viewer
from background.helper.socket_process import create_client, run_forever
from controller.auth_controller import verify_code_from_tiktok

LABEL = "MESSAGE PROCESS"
DEFAULT_AVATAR = "https://via.placeholder.com/150"

sio = create_client(LABEL)


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