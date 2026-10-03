import asyncio
import websockets
import json

async def listen(socketio):
    uri = "ws://localhost:21213/"
    async with websockets.connect(uri) as websocket:
        print("Connected to TikFinity!")
        async for message in websocket:
            data = json.loads(message)
            socketio.emit('new_comment', data)

def run_tikfinity_listener(socketio):
    asyncio.run(listen(socketio))