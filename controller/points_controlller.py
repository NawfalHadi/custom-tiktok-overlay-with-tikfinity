import csv
from datetime import datetime
from pathlib import Path

from utils.db import db_connection, find_viewer_detail, get_top_viewers

BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
TOP_N = 3


def get_all_time_top(limit=TOP_N):
    """Sang Satria Sedunia: top viewers by total points from tb_stats."""
    with db_connection() as conn:
        return get_top_viewers(conn, limit)


def get_today_top(limit=TOP_N):
    """Prajurit Hari Ini: top viewers by points earned today, from the daily CSV."""
    today = datetime.now().strftime("%Y-%m-%d")
    path = BIN_DIR / f"prajurit_points_daily_{today}.csv"
    if not path.exists():
        return []

    with open(path, encoding="utf-8") as f:
        rows = [
            {"username": r["username"], "points": int(r["points_today"])}
            for r in csv.DictReader(f)
        ]

    rows.sort(key=lambda r: r["points"], reverse=True)
    top = [
        {"rank": i + 1, "username": r["username"], "points": r["points"], "avatar": ""}
        for i, r in enumerate(rows[:limit])
    ]

    # The CSV has no avatars, so look them up in viewers.db
    with db_connection() as conn:
        for row in top:
            detail = find_viewer_detail(conn, row["username"])
            if detail and detail[2]:
                row["avatar"] = detail[2]
    return top


def get_leaderboards():
    """Both boards in one dict, ready to send to the overlay."""
    return {
        "all_time": get_all_time_top(),
        "today": get_today_top(),
    }