from flask import Blueprint, jsonify, render_template, request

from background.streak_process import log_and_calculate_streak
from utils.state import upeti_state
from utils.extensions import socketio

gift_bp = Blueprint("gift", __name__)

STREAK_TARGET_COINS = 5  # Threshold for the Upeti transition


@gift_bp.route("/api/upeti/toggle", methods=["POST"])
def toggle_upeti_state():
    data = request.get_json() or {}
    upeti_state["active"] = data.get("active", not upeti_state["active"])

    socketio.emit("trigger_upeti_transition", upeti_state)
    socketio.emit("update_upeti_state", upeti_state)
    return jsonify({"success": True, "active": upeti_state["active"]})


@gift_bp.route("/api/gift-event", methods=["POST"])
def gift_event_endpoint():
    data = request.get_json() or {}
    username = data.get("username", "User")
    avatar_url = data.get("avatarUrl", "")
    gift_name = data.get("giftName", "Gift")
    diamond_count = int(data.get("diamondCount", 1))
    repeat_count = int(data.get("repeatCount", 1))

    # Log to CSV and get the total for the 5-second window
    total_streak = log_and_calculate_streak(username, diamond_count, repeat_count)

    # Always update the HUD progress bar
    socketio.emit("streak_update", {
        "username": username,
        "avatarUrl": avatar_url,
        "currentCoins": total_streak,
        "targetCoins": STREAK_TARGET_COINS,
        "giftName": gift_name,
    })

    # Full Upeti transition only when the target is reached
    if total_streak >= STREAK_TARGET_COINS:
        upeti_state.update({
            "username": username,
            "avatarUrl": avatar_url,
            "giftName": gift_name,
            "giftCount": total_streak,
            "active": True,
        })
        socketio.emit("trigger_upeti_transition", upeti_state)
        socketio.emit("update_upeti_state", upeti_state)

    return jsonify({"status": "success", "total_streak": total_streak}), 200


@gift_bp.route("/breaktriger", methods=["POST"])
def break_trigger():
    data = request.get_json() or {}
    socketio.emit("trigger_transition", {
        "username": data.get("username", "UNKNOWN"),
        "avatarUrl": data.get("avatarUrl", "https://via.placeholder.com/150"),
    })
    return jsonify({"status": "success"}), 200


@gift_bp.route("/api/fake-trigger", methods=["POST"])
def fake_trigger():
    payload = request.get_json() or {}
    socketio.emit("tiktok_event", payload)
    return jsonify({"status": "success", "event": payload.get("event")}), 200


@gift_bp.route("/fake-api-panel")
def fake_api_panel():
    return render_template("templates/controls/api-panel.html")


@gift_bp.route("/upeti-transition")
def upeti_transition_page():
    return render_template("templates/upeti-transition.html")