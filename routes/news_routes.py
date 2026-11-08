import threading

from flask import Blueprint, jsonify, render_template, request

from utils.extensions import socketio
from routes.dashboard_routes import role_required

news_bp = Blueprint("news", __name__)

# Must match the transition animation length (3.6s in news-transition.html)
TRANSITION_DURATION = 3.6


@news_bp.route("/admin/news")
def news_panel():
    """News input panel (news-panel.html)."""
    return render_template("templates/news/news-panel.html")


@news_bp.route("/news-transition")
def news_transition_page():
    """Transition source for OBS (news-transition.html)."""
    return render_template("templates/news/news-transition.html")


@news_bp.route("/news-overlay")
def news_overlay_page():
    """Presenter overlay source for OBS (news-overlay.html)."""
    return render_template("templates/news/news-overlay.html")


@news_bp.route("/api/admin/news", methods=["POST"])
@role_required(1)
def api_submit_news():
    """
    Submit a news item (Role 1 only).
    Flow: news_transition -> (after animation) news_overlay.
    """
    data = request.get_json() or {}

    text = (data.get("text") or "").strip()
    subtext = (data.get("subtext") or "").strip()
    transition_image = (data.get("transitionImage") or "").strip()
    overlay_image = (data.get("overlayImage") or "").strip() or None
    highlight_text = (data.get("highlightText") or "").strip()

    if not text:
        return jsonify({"success": False, "message": "News text wajib diisi!"}), 400
    if not transition_image:
        return jsonify({"success": False, "message": "Transition image wajib diisi!"}), 400

    # 1. Play transition (image only)
    socketio.emit("news_transition", {"image": transition_image})

    # 2. After the transition finishes, show the overlay
    overlay_payload = {
        "text": text,
        "subtext": subtext,
        "image": overlay_image,
        "title": highlight_text,
    }
    threading.Timer(TRANSITION_DURATION, socketio.emit,
                    args=("news_overlay", overlay_payload)).start()

    return jsonify({"success": True, "message": "News dikirim ke layar!"})


@news_bp.route("/api/admin/news/hide", methods=["POST"])
@role_required(1)
def api_hide_news():
    """Hide the news overlay (Role 1 only)."""
    socketio.emit("news_hide", {})
    return jsonify({"success": True, "message": "News disembunyikan."})