from flask import Blueprint, render_template

overlay_bp = Blueprint("overlay", __name__)

@overlay_bp.route("/")
def overlay_home():
    return render_template("templates/scene/home.html")

@overlay_bp.route("/control")
def control_panel():
    return render_template("templates/dashboard/control.html")


@overlay_bp.route("/comments-overlay")
def comments_overlay():
    return render_template("templates/comments.html")

@overlay_bp.route("/upeti")
def upeti_page():
    return render_template("templates/overlay/upeti.html")

@overlay_bp.route("/upeti-transition")
def upeti_transition_page():
    return render_template("templates/overlay/upeti-transition.html")

@overlay_bp.route("/kaisars")
def kaisars_page():
    return render_template("templates/overlay/kaisars.html")

@overlay_bp.route("/transition")
def transition_overlay():
    return render_template("templates/overlay/kaisar-transition.html")

@overlay_bp.route("/ending")
def ending_page():
    return render_template("templates/scene/ending.html")