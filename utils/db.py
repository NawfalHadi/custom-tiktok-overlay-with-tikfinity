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

def find_viewer_detail(connection, username):
    """Return detailed information about a viewer, including their points."""
    return connection.execute(
        """
        SELECT v.id, v.username, v.profile_picture_url, s.points
        FROM tb_viewers AS v
        JOIN tb_stats AS s ON v.id = s.id_viewer
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

def update_profile_picture_viewer(connection, username, new_profile_url):
    """Update a viewer's profile picture no more than once every 60 seconds."""
    cursor = connection.execute(
        """
        UPDATE tb_stats
        SET last_refresh_picture = CURRENT_TIMESTAMP
        WHERE id_viewer = (
            SELECT id FROM tb_viewers WHERE LOWER(username) = LOWER(?)
        )
        AND (
            last_refresh_picture IS NULL
            OR last_refresh_picture <= datetime('now', '-1 day')
        )
        """,
        (username,),
    )
    if cursor.rowcount == 0:
        return False

    connection.execute(
        "UPDATE tb_viewers SET profile_picture_url = ? WHERE LOWER(username) = LOWER(?)",
        (new_profile_url, username),
    )
    return True

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

def get_top_viewers(connection, limit=3):
    """Return the top viewers by total points from tb_stats."""
    rows = connection.execute(
        """
        SELECT v.username, v.profile_picture_url, s.points
        FROM tb_stats AS s
        JOIN tb_viewers AS v ON v.id = s.id_viewer
        ORDER BY s.points DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        {"rank": i + 1, "username": r[0], "avatar": r[1] or "", "points": r[2]}
        for i, r in enumerate(rows)
    ]