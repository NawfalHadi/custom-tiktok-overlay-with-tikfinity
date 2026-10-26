from utils.db import db_connection


def calculate_message_cost(message):
    """500 Pts for the first 10 words, plus 500 Pts for each extra 10 words."""
    words = len(message.split())
    if words <= 0:
        return 500
    tiers = (words - 1) // 10
    return 500 + tiers * 500


def deduct_points(user_id, cost):
    """Subtract cost only if the user can afford it.
    Returns (success, points_after_the_attempt)."""
    with db_connection() as conn:
        cursor = conn.execute(
            "UPDATE tb_stats SET points = points - ? WHERE id_viewer = ? AND points >= ?",
            (cost, user_id, cost),
        )
        row = conn.execute(
            "SELECT points FROM tb_stats WHERE id_viewer = ?", (user_id,)
        ).fetchone()

    current = row[0] if row and row[0] is not None else 0
    return cursor.rowcount > 0, current

def add_history_entry(user_id, message):
    """Add a history entry for the user."""
    with db_connection() as conn:
        conn.execute(
            "INSERT INTO tb_history (id_viewer, message) VALUES (?, ?)",
            (user_id, message),
        )