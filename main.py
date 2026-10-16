import threading
import logging
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_socketio import SocketIO
from pathlib import Path
import sqlite3

# Background Functions
from background.gift_process import run_gift_inspector
from background.message_process import run_message_process
from background.point_process import run_point_inspector
from background.streak_process import log_and_calculate_streak
from controller.auth_controller import create_pending_registration, authenticate_user

from listener import run_tikfinity_listener

# 1. Import the initialization function
from datas.init import initialize_database
# 2. Run database initialization BEFORE anything else starts
initialize_database()

app = Flask(__name__, template_folder='.')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', transports=['websocket', 'polling'])

logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)
logging.getLogger('socketio').setLevel(logging.ERROR)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    transports=['websocket', 'polling'],
    logger=False,
    engineio_logger=False
)

DB_PATH = str(Path('datas') / 'viewers.db')

# ============== Authentication Routes ==============
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"success": False, "message": "Email dan Password wajib diisi!"}), 400

        # Generate 6-digit code & simpan sementara di local JSON (termasuk hash password)
        verify_code = create_pending_registration(email, password)

        # PASTIKAN verify_code dikirim ke frontend agar card-nya muncul!
        return jsonify({
            "success": True, 
            "verify_code": verify_code,
            "message": f"Silakan ketik !verify {verify_code} di TikTok Live!"
        }), 200

    return render_template('templates/auth/register.html') # Sesuaikan path foldermu

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"success": False, "message": "Email dan Password wajib diisi!"}), 400

        user = authenticate_user(email, password)
        if user:
            # Simpan session login
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({"success": True, "message": "Login Berhasil!", "redirect": "/dashboard/telling"}), 200
        else:
            return jsonify({"success": False, "message": "Email atau Password salah!"}), 401

    return render_template('templates/auth/login.html')

@app.route('/dashboard/telling')
def dashboard_telling():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.username, v.email, v.profile_picture_url, s.points 
        FROM tb_viewers v
        LEFT JOIN tb_stats s ON v.id = s.id_viewer
        WHERE v.id = ?
    """, (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if not user_data:
        session.clear()
        return redirect('/login')

    return render_template('templates/dashboard/telling.html', user=dict(user_data))

@app.route('/dashboard/alerting')
def dashboard_alerting():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.username, v.email, v.profile_picture_url, s.points 
        FROM tb_viewers v
        LEFT JOIN tb_stats s ON v.id = s.id_viewer
        WHERE v.id = ?
    """, (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if not user_data:
        session.clear()
        return redirect('/login')

    return render_template('templates/dashboard/alerting.html', user=dict(user_data))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ============== Alert Routes ============
@socketio.on('message_alert')
def handle_message_alert(data):
    # Broadcast the message alert to all connected overlay clients
    socketio.emit('message_alert', data)

@socketio.on('media_alert')
def handle_media_alert(data):
    # Broadcast the media/rickroll alert to all connected overlay clients
    socketio.emit('media_alert', data)

@app.route('/msg-alert')
def msg_alert_overlay():
    return render_template('templates/alert/message_alert.html')

@app.route('/media-alert')
def media_alert_overlay():
    return render_template('templates/alert/media_alert.html')


@app.route('/api/members', methods=['GET'])
def get_members():
    search = request.args.get('search', '').strip()
    sort_dir = request.args.get('sort', 'desc').lower()
    filter_announced = request.args.get('announced', '') # '0', '1', or ''

    # Base query joining members with viewers to get the username
    query = '''
        SELECT m.id, m.id_viewer, v.username, v.profile_picture_url, m.is_announced, m.created_at, m.joined_at
        FROM tb_members m
        JOIN tb_viewers v ON m.id_viewer = v.id
        WHERE 1=1
    '''
    params = []

    if search:
        query += ' AND v.username LIKE ?'
        params.append(f'%{search}%')

    if filter_announced in ['0', '1']:
        query += ' AND m.is_announced = ?'
        params.append(int(filter_announced))

    order = 'ASC' if sort_dir == 'asc' else 'DESC'
    query += f' ORDER BY m.created_at {order}'

    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    members = [dict(row) for row in rows]
    return jsonify(members)

@app.route('/api/members/<int:member_id>/announce', methods=['POST'])
def toggle_announce(member_id):
    data = request.get_json() or {}
    new_status = data.get('is_announced', 1)

    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute('UPDATE tb_members SET is_announced = ? WHERE id = ?', (new_status, member_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "member_id": member_id, "is_announced": new_status})

@app.route('/control')
def control_panel():
    return render_template('templates/control.html')

# ============== Overlays ==============

@app.route('/comments-overlay')
def comments_overlay():
    return render_template('templates/comments.html')

@app.route('/info')
def info_page():
    return render_template('templates/info.html')

@app.route('/transition')
def transition_overlay():
    return render_template('templates/transition.html')

@app.route('/upeti')
def upeti_page():
    return render_template('templates/upeti.html')

@app.route('/kaisars')
def kaisars_page():
    return render_template('templates/kaisars.html')

@app.route('/breaktriger', methods=['POST'])
def break_trigger():
    data = request.get_json() or {}
    username = data.get('username', 'UNKNOWN')
    avatar_url = data.get('avatarUrl', 'https://via.placeholder.com/150')
    
    socketio.emit('trigger_transition', {
        'username': username,
        'avatarUrl': avatar_url
    })
    return jsonify({"status": "success"}), 200

# ==================== Upeti Actions & Gift Events ====================

@app.route('/api/upeti/toggle', methods=['POST'])
def toggle_upeti_state():
    data = request.get_json() or {}
    new_active_status = data.get("active", not upeti_state["active"])
    
    upeti_state["active"] = new_active_status

    socketio.emit('trigger_upeti_transition', upeti_state)
    socketio.emit('update_upeti_state', upeti_state)
    return jsonify({"success": True, "active": upeti_state["active"]})

@app.route('/api/gift-event', methods=['POST'])
def gift_event_endpoint():
    data = request.get_json() or {}
    username = data.get("username", "User")
    avatar_url = data.get("avatarUrl", "")
    gift_name = data.get("giftName", "Gift")
    diamond_count = int(data.get("diamondCount", 1))
    repeat_count = int(data.get("repeatCount", 1))

    # 1. Log to CSV once and calculate total streak for the 5-second window
    total_streak = log_and_calculate_streak(username, diamond_count, repeat_count)
    target_coins = 5  # Threshold target for Upeti transition

    # 2. ALWAYS broadcast live progress bar updates to the HUD overlay
    socketio.emit('streak_update', {
        "username": username,
        "avatarUrl": avatar_url,
        "currentCoins": total_streak,
        "targetCoins": target_coins,
        "giftName": gift_name
    })

    # 3. ONLY trigger full Upeti transition if the 20-coin target is reached/crossed
    if total_streak >= target_coins:
        upeti_state["username"] = username
        upeti_state["avatarUrl"] = avatar_url
        upeti_state["giftName"] = gift_name
        upeti_state["giftCount"] = total_streak
        upeti_state["active"] = True

        socketio.emit('trigger_upeti_transition', upeti_state)
        socketio.emit('update_upeti_state', upeti_state)

    return jsonify({"status": "success", "total_streak": total_streak}), 200

@app.route('/upeti-transition')
def upeti_transition_page():
    return render_template('templates/upeti-transition.html')

# =============== Controls Route ============
@app.route('/fake-api-panel')
def fake_api_panel():
    return render_template('templates/controls/api-panel.html')

@app.route('/api/fake-trigger', methods=['POST'])
def fake_trigger():
    payload = request.get_json() or {}
    socketio.emit('tiktok_event', payload)
    return jsonify({"status": "success", "event": payload.get("event")}), 200

# ============= HUD Route ============
@app.route('/gift-hud')
def gift_hud_page():
    return render_template('templates/hud/gift-hud.html')

# =============== Scene Route ============
@app.route('/ending')
def ending_page():
    return render_template('templates/scene/ending.html')


if __name__ == '__main__':

    upeti_state = {
        "active": True,
        "username": "pementolan",
        "avatarUrl": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&auto=format&fit=crop&q=80",
        "giftName": "Galaxy",
        "giftCount": 1,
        "giftIconUrl": "https://img.icons8.com/color/96/gift.png"
    }

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