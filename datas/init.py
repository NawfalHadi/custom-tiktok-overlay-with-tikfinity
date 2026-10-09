import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().with_name("viewers.db")


def initialize_database():
	with sqlite3.connect(DB_PATH) as connection:
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS tb_viewers (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT NOT NULL,
				email TEXT,
				verify_code TEXT,
				created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
				updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
			)
			"""
		)


if __name__ == "__main__":
	initialize_database()
