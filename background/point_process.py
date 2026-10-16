import sqlite3
import time
from pathlib import Path
import socketio

sio = socketio.Client()
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "datas" / "viewers.db"

COIN_TO_POINT_MULTIPLIER = 100
MEMBER_POINT_MULTIPLIER = 1.2

# Konfigurasi Anti-Spam Chat
CHAT_POINT_REWARD = 10       # Jumlah poin yang didapat per chat valid
COOLDOWN_SECONDS = 30.0      # Jeda waktu minimum antar chat per user (dalam detik)
MIN_MESSAGE_LENGTH = 3       # Panjang minimum karakter pesan agar tidak di-spam

# Cache untuk melacak waktu chat terakhir setiap user: { "username": timestamp }
last_chat_times = {}

def award_points(username, coin_value, gift_multiplier=1):
	with sqlite3.connect(DB_PATH) as connection:
		viewer = connection.execute(
			"""
			SELECT v.id, EXISTS(
				SELECT 1 FROM tb_members AS m WHERE m.id_viewer = v.id
			)
			FROM tb_viewers AS v
			WHERE LOWER(v.username) = LOWER(?)
			""",
			(username,),
		).fetchone()

		if viewer is None:
			return

		multiplier = (MEMBER_POINT_MULTIPLIER if viewer[1] else 1) * gift_multiplier
		points = int(coin_value * COIN_TO_POINT_MULTIPLIER * multiplier)
		connection.execute(
			"""
			INSERT INTO tb_stats (id_viewer, points) VALUES (?, ?)
			ON CONFLICT(id_viewer) DO UPDATE SET points = points + excluded.points
			""",
			(viewer[0], points),
		)

def award_chat_points(username):
	"""Memberikan poin chat dengan proteksi cooldown anti-spam."""
	global last_chat_times
	current_time = time.time()
	
	# Cek cooldown user
	if username in last_chat_times:
		elapsed = current_time - last_chat_times[username]
		if elapsed < COOLDOWN_SECONDS:
			# Masih dalam masa cooldown, abaikan (mencegah spam)
			return False

	# Update waktu chat terakhir user
	last_chat_times[username] = current_time

	with sqlite3.connect(DB_PATH) as connection:
		viewer = connection.execute(
			"""
			SELECT v.id, EXISTS(
				SELECT 1 FROM tb_members AS m WHERE m.id_viewer = v.id
			)
			FROM tb_viewers AS v
			WHERE LOWER(v.username) = LOWER(?)
			""",
			(username,),
		).fetchone()

		if viewer is None:
			return False

		# Member member mendapatkan bonus multiplier juga untuk chat
		multiplier = MEMBER_POINT_MULTIPLIER if viewer[1] else 1.0
		points = int(CHAT_POINT_REWARD * multiplier)

		connection.execute(
			"""
			INSERT INTO tb_stats (id_viewer, points) VALUES (?, ?)
			ON CONFLICT(id_viewer) DO UPDATE SET points = points + excluded.points
			""",
			(viewer[0], points),
		)
	return True

@sio.on("connect")
def on_connect():
	print("-> [POINT PROCESSOR] Connected to Flask Socket.IO server!")

@sio.on("disconnect")
def on_disconnect():
	print("-> [POINT PROCESSOR] Disconnected from server.")

@sio.on("tiktok_event")
def handle_tiktok_event(res):
	try:
		event_type = res.get("event")
		data = res.get("data", {})

		# 1. Handle Event Gift (Logika lama tetap aman)
		if event_type == "gift":
			diamond_count = int(data.get("diamondCount", 0))
			coin_value = diamond_count
			username = data.get("uniqueId") or data.get("nickname") or "User"
			
			if coin_value < 5:
				output = "small gift"
				gift_multiplier = 1
			elif coin_value < 20:
				output = "medium gift"
				gift_multiplier = 1.15
			elif coin_value < 50:
				output = "large gift"
				gift_multiplier = 1.2
			else:
				output = "special gift"
				gift_multiplier = 1.4

			award_points(username, coin_value, gift_multiplier)
			print(f"-> [POINT PROCESSOR] {username} sent a {output} ({coin_value} coins)")

		# 2. Handle Event Chat (Fitur Baru dengan Anti-Spam)
		elif event_type in ["chat", "comment"]:
			username = data.get("uniqueId") or data.get("nickname") or "User"
			message = data.get("comment") or data.get("message") or ""

			# Abaikan jika pesan terlalu pendek (mencegah spam huruf/emoji tunggal)
			if len(message.strip()) < MIN_MESSAGE_LENGTH:
				return

			# Abaikan jika pesan berupa command sistem (seperti !verify atau !join)
			if message.strip().startswith("!"):
				return

			# Coba berikan poin berdasarkan cooldown
			success = award_chat_points(username)
			if success:
				print(f"-> [CHAT POINT] @{username} mendapat poin karena aktif mengobrol.")

	except (TypeError, ValueError) as error:
		print(f"-> [POINT PROCESSOR] Invalid value: {error}")
	except Exception as error:
		print(f"-> [POINT PROCESSOR] Failed to process event: {error}")

def run_point_inspector():
	while True:
		try:
			print("-> [POINT PROCESSOR] Connecting to Flask server on port 5000...")
			sio.connect("http://127.0.0.1:5000", transports=["polling"])
			sio.wait()
		except Exception as error:
			print(
				f"-> [POINT PROCESSOR] Connection error: {error}. "
				"Reconnecting in 5s..."
			)
			time.sleep(5)

if __name__ == "__main__":
	run_point_inspector()