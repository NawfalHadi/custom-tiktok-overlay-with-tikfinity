from flask import Blueprint, render_template

overlay_bp = Blueprint("overlay", __name__)


@overlay_bp.route("/control")
def control_panel():
    return render_template("templates/control.html")


@overlay_bp.route("/comments-overlay")
def comments_overlay():
    return render_template("templates/comments.html")


@overlay_bp.route("/transition")
def transition_overlay():
    return render_template("templates/transition.html")


@overlay_bp.route("/upeti")
def upeti_page():
    return render_template("templates/upeti.html")


@overlay_bp.route("/kaisars")
def kaisars_page():
    return render_template("templates/kaisars.html")


@overlay_bp.route("/ending")
def ending_page():
    return render_template("templates/scene/ending.html")