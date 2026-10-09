import asyncio
import websockets
import json

async def inspect_gifts():
    uri = "ws://localhost:21213/"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("-> [GIFT INSPECTOR] Connected to TikFinity!")
                async for message in websocket:
                    res = json.loads(message)
                    if res.get("event") == "gift":
                        gift = res.get("data", {})
                        username = gift.get("nickname", "Unknown user")
                        unique_id = gift.get("uniqueId")
                        gift_name = gift.get("giftName", "Unknown gift")
                        count = gift.get("repeatCount", 1)
                        diamonds = gift.get("diamondCount", 0)

                        print("\n=== GIFT RECEIVED ===")
                        print(f"From: {username}" + (f" (@{unique_id})" if unique_id else ""))
                        print(f"Gift: {gift_name} × {count}")
                        print(f"Diamonds: {diamonds}")
        except Exception as e:
            print(f"-> [GIFT INSPECTOR] Error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

# This wrapper function MUST be outside __main__ so main.py can call it
def run_gift_inspector():
    asyncio.run(inspect_gifts())

if __name__ == "__main__":
    run_gift_inspector()