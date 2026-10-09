import asyncio
import websockets
import json

async def process_messages():
    uri = "ws://localhost:21213/"
    seen_messages = set()
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to TikFinity! Listening for comments...")
            async for message in websocket:
                try:
                    res = json.loads(message)
                    event = res.get("event")
                    if event == "chat" or event == "comment":
                        d = res.get("data", {})
                        user = d.get("nickname") or d.get("uniqueId") or "User"
                        msg = d.get("comment", "")

                        message_id = d.get("id") or d.get("commentId") or d.get("messageId") or (user, msg)
                        if message_id in seen_messages:
                            continue
                        seen_messages.add(message_id)

                        print(f"{user}: {msg}")
                except Exception as e:
                    print(f"Error parsing message: {e}")
    except Exception as e:
        print(f"Connection error: {e}")

def run_message_process():
    asyncio.run(process_messages())

if __name__ == "__main__":
    run_message_process()