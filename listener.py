import asyncio
import websockets
import json

async def listen(socketio):
    uri = "ws://localhost:21213/"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to TikFinity!")
                async for message in websocket:
                    data = json.loads(message)
                    socketio.emit('tiktok_event', data)
        except Exception as e:
            print(f"Error connecting to TikFinity: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
            
def run_tikfinity_listener(socketio):
    asyncio.run(listen(socketio))