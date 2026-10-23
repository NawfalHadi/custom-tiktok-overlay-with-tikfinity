from pathlib import Path

# background/helper/config.py -> project root is three levels up
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = Path("datas") / "viewers.db"

SERVER_URL = "http://127.0.0.1:5000"
RECONNECT_DELAY = 5  # seconds

# Gift IDs
MEMBER_GIFT_ID = 7934

# Points
COIN_TO_POINT_MULTIPLIER = 50
MEMBER_POINT_MULTIPLIER = 1.2

# Chat anti-spam
CHAT_POINT_REWARD = 50
COOLDOWN_SECONDS = 30.0
MIN_MESSAGE_LENGTH = 3

# Daily check-in
DAILY_POINT_REWARD = 250

# Watch time (passive points)
WATCH_TIME_INTERVAL = 300   # 5 minutes
WATCH_TIME_REWARD = 20
ACTIVITY_TIMEOUT = 900      # 15 minutes