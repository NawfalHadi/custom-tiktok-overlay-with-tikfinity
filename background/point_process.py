import sqlite3
import time
from pathlib import Path

import socketio


sio = socketio.Client()
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "datas" / "viewers.db"

COIN_TO_POINT_MULTIPLIER = 100
MEMBER_POINT_MULTIPLIER = 1.2


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


@sio.on("connect")
def on_connect():
	print("-> [POINT PROCESSOR] Connected to Flask Socket.IO server!")


@sio.on("disconnect")
def on_disconnect():
	print("-> [POINT PROCESSOR] Disconnected from server.")


@sio.on("tiktok_event")
def handle_tiktok_event(res):
	try:
		if res.get("event") != "gift":
			return

		gift_data = res.get("data", {})
		diamond_count = int(gift_data.get("diamondCount", 0))
		coin_value = diamond_count
		username = gift_data.get("uniqueId") or gift_data.get("nickname") or "User"
		
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

		print(
			f"-> [POINT PROCESSOR] {username} sent a {output} "
			f"({coin_value} coins)"
		)
	except (TypeError, ValueError) as error:
		print(f"-> [POINT PROCESSOR] Invalid gift coin value: {error}")
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
