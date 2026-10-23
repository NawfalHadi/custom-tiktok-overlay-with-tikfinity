import time

import socketio

from utills.config import RECONNECT_DELAY, SERVER_URL


def create_client(label):
    """Create a Socket.IO client with connect/disconnect logging.
    Each process registers its own @sio.on('tiktok_event') handler on the returned client."""
    sio = socketio.Client()

    @sio.event
    def connect():
        print(f"-> [{label}] Connected to Flask Socket.IO server!")

    @sio.event
    def disconnect():
        print(f"-> [{label}] Disconnected from server.")

    return sio


def run_forever(sio, label, transports=("polling",)):
    """Connect and wait, reconnecting after any error or disconnect."""
    while True:
        try:
            print(f"-> [{label}] Connecting to {SERVER_URL}...")
            sio.connect(SERVER_URL, transports=list(transports))
            sio.wait()
        except Exception as error:
            print(f"-> [{label}] Connection error: {error}. Reconnecting in {RECONNECT_DELAY}s...")
        time.sleep(RECONNECT_DELAY)