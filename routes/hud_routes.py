from flask import Blueprint, render_template, jsonify, request
from utils.extensions import socketio

hud_bp = Blueprint("hud", __name__)

@hud_bp.route("/api/trigger/points", methods=["POST"])
def trigger_points():
    data = request.get_json() or {}

    socketio.emit("trigger_points_check", {
        "username": data.get("username", "User"),
        "points": data.get("points", 0),
        "avatarUrl": data.get("avatarUrl", ""),
    })

    return jsonify({"success": True})

@hud_bp.route("/gift-hud")
def gift_hud_page():
    return render_template("templates/hud/gift-hud.html")

@hud_bp.route("/info")
def info_page():
    """Join notification HUD."""
    return render_template("templates/hud/join-hud.html")

# You can also add a route or view here if you render the points check banner page directly
@hud_bp.route("/points-hud")
def points_check_hud_page():
    return render_template("templates/hud/points-hud.html")