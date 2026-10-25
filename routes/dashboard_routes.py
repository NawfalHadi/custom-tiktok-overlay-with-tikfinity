import sqlite3

from flask import Blueprint, redirect, render_template, session, request, jsonify
from controller.admin_controller import (
    get_admin_viewers_data,
    update_viewer_role,
    toggle_viewer_membership
)

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




@dashboard_bp.route("/dashboard")
def get_profile():
    return _render_dashboard("templates/dashboard/profiles.html")


@dashboard_bp.route("/dashboard/alerting")
def dashboard_alerting():
    return _render_dashboard("templates/dashboard/alerting.html")

@dashboard_bp.route("/admin/control")
def admin_control_panel():
    """Renders the admin control panel template (admin-panel.html)."""
    return render_template("templates/controls/admin-panel.html")

@dashboard_bp.route("/api/admin/viewers", methods=["GET"])
def api_get_viewers():
    """
    API endpoint providing paginated, sorted, and searched viewers list,
    along with points from tb_stats and member status from tb_members.
    """
    result = get_admin_viewers_data(request.args)
    return jsonify(result)

@dashboard_bp.route("/api/admin/viewers/<int:viewer_id>/role", methods=["POST"])
def api_update_role(viewer_id):
    """Updates a viewer's role ID in tb_viewers."""
    data = request.get_json() or {}
    role_id = data.get("role_id")
    update_viewer_role(viewer_id, role_id)
    return jsonify({"success": True})

@dashboard_bp.route("/api/admin/viewers/<int:viewer_id>/toggle-member", methods=["POST"])
def api_toggle_member(viewer_id):
    """Toggles a viewer's presence inside tb_members."""
    is_member = toggle_viewer_membership(viewer_id)
    return jsonify({"success": True, "is_member": is_member})