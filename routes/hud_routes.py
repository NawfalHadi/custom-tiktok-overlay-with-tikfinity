from flask import Blueprint, render_template

hud_bp = Blueprint("hud", __name__)


@hud_bp.route("/gift-hud")
def gift_hud_page():
    return render_template("templates/hud/gift-hud.html")

@hud_bp.route("/info")
def info_page():
    """Join notification HUD."""
    return render_template("templates/hud/join-hud.html")