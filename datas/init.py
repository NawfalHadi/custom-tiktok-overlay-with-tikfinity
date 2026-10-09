import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().with_name("viewers.db")


def initialize_database():
	with sqlite3.connect(DB_PATH) as connection:
		connection.execute("PRAGMA foreign_keys = ON")
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
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS tb_members (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				id_viewer INTEGER NOT NULL UNIQUE,
				is_announced INTEGER NOT NULL DEFAULT 0 CHECK (is_announced IN (0, 1)),
				created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
				joined_at TEXT,
				FOREIGN KEY (id_viewer) REFERENCES tb_viewers(id) ON DELETE CASCADE
			)
			"""
		)


if __name__ == "__main__":
	initialize_database()
