import sqlite3

from flask import Blueprint, jsonify, request

from utils.db import db_connection

member_bp = Blueprint("member", __name__)


@member_bp.route("/api/members", methods=["GET"])
def get_members():
    search = request.args.get("search", "").strip()
    sort_dir = request.args.get("sort", "desc").lower()
    filter_announced = request.args.get("announced", "")  # "0", "1", or ""

    query = """
        SELECT m.id, m.id_viewer, v.username, v.profile_picture_url,
               m.is_announced, m.created_at, m.joined_at
        FROM tb_members m
        JOIN tb_viewers v ON m.id_viewer = v.id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND v.username LIKE ?"
        params.append(f"%{search}%")

    if filter_announced in ("0", "1"):
        query += " AND m.is_announced = ?"
        params.append(int(filter_announced))

    order = "ASC" if sort_dir == "asc" else "DESC"
    query += f" ORDER BY m.created_at {order}"

    with db_connection() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()

    return jsonify([dict(row) for row in rows])


@member_bp.route("/api/members/<int:member_id>/announce", methods=["POST"])
def toggle_announce(member_id):
    data = request.get_json() or {}
    new_status = data.get("is_announced", 1)

    with db_connection() as conn:
        conn.execute(
            "UPDATE tb_members SET is_announced = ? WHERE id = ?",
            (new_status, member_id),
        )

    return jsonify({"success": True, "member_id": member_id, "is_announced": new_status})