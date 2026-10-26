from flask import Blueprint, jsonify, render_template, request, session

from controller.alert_controller import add_history_entry, calculate_message_cost, deduct_points
from utils.extensions import socketio

alert_bp = Blueprint("alert", __name__)


@alert_bp.route("/api/trigger/msg-alert", methods=["POST"])
def trigger_msg_alert():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"success": False, "message": "Pesan tidak boleh kosong!"}), 400

    # Cost is calculated on the server, so the client can't change it
    cost = calculate_message_cost(message)
    success, points = deduct_points(session["user_id"], cost)

    if not success:
        return jsonify({
            "success": False,
            "message": f"Poin Anda tidak cukup! Butuh {cost:,} Pts, poin Anda saat ini {points:,} Pts.",
        }), 400
    else:
        add_history_entry(session["user_id"], message)

    socketio.emit("message_alert", {
        "username": session.get("username", "Kesatria"),
        "message": message,
    })

    return jsonify({
        "success": True,
        "message": "Alert berhasil dikirim ke layar!",
        "remaining_points": points,
    }), 200


@alert_bp.route("/msg-alert")
def msg_alert_overlay():
    return render_template("templates/alert/message_alert.html")