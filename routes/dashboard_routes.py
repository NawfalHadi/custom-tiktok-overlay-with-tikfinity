import sqlite3

from functools import wraps
from flask import Blueprint, redirect, render_template, session, request, jsonify
from controller.admin_controller import (
    get_admin_viewers_data,
    update_viewer_role,
    toggle_viewer_membership,
    add_points_to_viewer,
    create_role
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

def role_required(required_role=1):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            print(f"DEBUG SESSION -> user_id: {session.get('user_id')}, id_role: {session.get('id_role')}")
            
            if 'user_id' not in session:
                return jsonify({"success": False, "message": "Unauthorized. Please login."}), 401
            
            user_role = session.get('id_role')
            if user_role != required_role:
                return jsonify({
                    "success": False, 
                    "message": f"Access denied! Required role: {required_role}, Your session role: {user_role}"
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def roles_allowed(*allowed_roles):
    """Page access: must be logged in and have one of the allowed roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                return redirect("/login")
            if session.get("id_role") not in allowed_roles:
                return "Access denied", 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- ADMIN ROUTES ---

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

# -- MODERATOR ROUTES (DIKUNCI: Wajib Role 1 & 2) ---

@dashboard_bp.route("/moderator/control")
@roles_allowed(1, 2)  # 1 = admin, 2 = moderator
def moderator_control_panel():
    """Renders the moderator panel (moderator-panel.html)."""
    return render_template("templates/controls/mod-panel.html")

@dashboard_bp.route("/api/moderator/viewers", methods=["GET"])
@roles_allowed(1, 2)  # admin + moderator, read-only
def api_moderator_viewers():
    """Read-only viewers list for the moderator panel (same data as admin, no mutations)."""
    return jsonify(get_admin_viewers_data(request.args))

# --- MUTATION / EDIT ROUTES (DIKUNCI: Wajib Role 1) ---

@dashboard_bp.route("/api/admin/viewers/<int:viewer_id>/role", methods=["POST"])
@role_required(1)
def api_update_role(viewer_id):
    """Mengubah role viewer (Hanya Role 1)."""
    data = request.get_json() or {}
    role_id = data.get("role_id")
    update_viewer_role(viewer_id, role_id)
    return jsonify({"success": True, "message": "Role berhasil diperbarui!"})

@dashboard_bp.route("/api/admin/viewers/<int:viewer_id>/toggle-member", methods=["POST"])
@role_required(1)
def api_toggle_member(viewer_id):
    """Menambah/menghapus member (Hanya Role 1)."""
    is_member = toggle_viewer_membership(viewer_id)
    return jsonify({"success": True, "is_member": is_member})

@dashboard_bp.route("/api/admin/viewers/<int:viewer_id>/add-points", methods=["POST"])
@role_required(1)
def api_add_points(viewer_id):
    """Menambahkan poin ke viewer (Hanya Role 1)."""
    data = request.get_json() or {}
    points = int(data.get("points", 0))
    if points > 0:
        add_points_to_viewer(viewer_id, points)
    return jsonify({"success": True, "message": "Poin berhasil ditambahkan!"})

@dashboard_bp.route("/api/admin/roles", methods=["POST"])
@role_required(1)
def api_create_role():
    """Membuat role baru di tb_roles (Hanya Role 1)."""
    data = request.get_json() or {}
    role_name = data.get("role_name", "").strip()
    if not role_name:
        return jsonify({"success": False, "error": "Nama role wajib diisi!"}), 400
    
    try:
        create_role(role_name)
        return jsonify({"success": True, "message": f"Role '{role_name}' berhasil dibuat!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400