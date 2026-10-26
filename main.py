import threading
import logging
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from pathlib import Path
import sqlite3

from utils.extensions import socketio
from utils.state import upeti_state

# Background Functions
from background.gift_process import run_gift_inspector
from background.message_process import run_message_process
from background.point_process import run_point_inspector
from background.streak_process import log_and_calculate_streak

from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.alert_routes import alert_bp
from routes.member_routes import member_bp
from routes.gift_routes import gift_bp
from routes.hud_routes import hud_bp
from routes.overlay_routes import overlay_bp

from listener import run_tikfinity_listener

from saweria_webhook import saweria_bp, init_saweria_socket

# 1. Import the initialization function
from datas.init import initialize_database
# 2. Run database initialization BEFORE anything else starts
initialize_database()

app = Flask(__name__, template_folder='.')


init_saweria_socket(socketio)

app.register_blueprint(saweria_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(alert_bp)
app.register_blueprint(member_bp)
app.register_blueprint(gift_bp)
app.register_blueprint(hud_bp)
app.register_blueprint(overlay_bp)

logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)
logging.getLogger('socketio').setLevel(logging.ERROR)

socketio.init_app(app)

DB_PATH = str(Path('datas') / 'viewers.db')


if __name__ == '__main__':

    app.secret_key = 'dgcb_secret_key_sangat_aman'

    listener_thread = threading.Thread(target=run_tikfinity_listener, args=(socketio,), daemon=True)
    listener_thread.start()

    message_thread = threading.Thread(target=run_message_process, daemon=True)
    message_thread.start()

    gift_thread = threading.Thread(target=run_gift_inspector, daemon=True)
    gift_thread.start()

    point_thread = threading.Thread(target=run_point_inspector, daemon=True)
    point_thread.start()

    socketio.run(app, host='0.0.0.0', port=5000, debug=False)