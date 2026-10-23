from flask_socketio import SocketIO

# Created without an app. main.py attaches it with socketio.init_app(app).
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",
    transports=["websocket", "polling"],
    logger=False,
    engineio_logger=False,
)