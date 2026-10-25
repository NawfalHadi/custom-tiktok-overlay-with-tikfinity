from flask import Blueprint, jsonify, redirect, render_template, request, session

from controller.auth_controller import authenticate_user, create_pending_registration

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = request.get_json() or {}
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"success": False, "message": "Email dan Password wajib diisi!"}), 400

        verify_code = create_pending_registration(email, password)
        return jsonify({
            "success": True,
            "verify_code": verify_code,
            "message": f"Silakan ketik !verify {verify_code} di TikTok Live!",
        }), 200

    return render_template("templates/auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json() or {}
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"success": False, "message": "Email dan Password wajib diisi!"}), 400

        user = authenticate_user(email, password)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["id_role"] = user.get("id_role", None)
            return jsonify({"success": True, "message": "Login Berhasil!", "redirect": "/dashboard"}), 200

        return jsonify({"success": False, "message": "Email atau Password salah!"}), 401

    return render_template("templates/auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")