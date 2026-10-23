import sqlite3
from contextlib import contextmanager

from utils.config import DB_PATH, MEMBER_POINT_MULTIPLIER


@contextmanager
def db_connection():
    """Open a connection, commit on success, roll back on error, always close."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def find_viewer(connection, username):
    """Return (id, last_daily_claim, is_member) or None. Case-insensitive."""
    return connection.execute(
        """
        SELECT v.id, v.last_daily_claim, EXISTS(
            SELECT 1 FROM tb_members AS m WHERE m.id_viewer = v.id
        )
        FROM tb_viewers AS v
        WHERE LOWER(v.username) = LOWER(?)
        """,
        (username,),
    ).fetchone()


def create_viewer(connection, username, profile_url):
    """Insert a viewer and their stats row. Returns the new viewer id."""
    cursor = connection.execute(
        "INSERT INTO tb_viewers (username, profile_picture_url) VALUES (?, ?)",
        (username, profile_url),
    )
    viewer_id = cursor.lastrowid
    connection.execute(
        "INSERT INTO tb_stats (id_viewer, points) VALUES (?, ?)",
        (viewer_id, 0),
    )
    return viewer_id


def add_member(connection, viewer_id):
    """Add a viewer to tb_members. Returns True if a row was inserted."""
    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO tb_members (id_viewer, joined_at)
        VALUES (?, CURRENT_TIMESTAMP)
        """,
        (viewer_id,),
    )
    return cursor.rowcount > 0


def member_multiplier(is_member):
    return MEMBER_POINT_MULTIPLIER if is_member else 1.0


def add_points(connection, viewer_id, points):
    connection.execute(
        """
        INSERT INTO tb_stats (id_viewer, points) VALUES (?, ?)
        ON CONFLICT(id_viewer) DO UPDATE SET points = points + excluded.points
        """,
        (viewer_id, points),
    )