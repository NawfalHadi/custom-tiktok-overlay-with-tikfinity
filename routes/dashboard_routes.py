import sqlite3

from flask import Blueprint, redirect, render_template, session

from utils.db import db_connection

dashboard_bp = Blueprint("dashboard", __name__)


def _load_user_profile(user_id):
    with db_connection() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("""
            SELECT v.username, v.email, v.profile_picture_url, s.points
            FROM tb_viewers v
            LEFT JOIN tb_stats s ON v.id = s.id_viewer
            WHERE v.id = ?
        """, (user_id,)).fetchone()
    return dict(row) if row else None


def _render_dashboard(template):
    if "user_id" not in session:
        return redirect("/login")

    user = _load_user_profile(session["user_id"])
    if not user:
        session.clear()
        return redirect("/login")

    return render_template(template, user=user)


@dashboard_bp.route("/dashboard/telling")
def get_profile():
    return _render_dashboard("templates/dashboard/telling.html")


@dashboard_bp.route("/dashboard/alerting")
def dashboard_alerting():
    return _render_dashboard("templates/dashboard/alerting.html")