import threading
import logging
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
from pathlib import Path
import sqlite3

# Background Function
from background.gift_process import run_gift_inspector
from background.message_process import run_message_process
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

@app.route('/api/members', methods=['GET'])
def get_members():
    search = request.args.get('search', '').strip()
    sort_dir = request.args.get('sort', 'desc').lower()
    filter_announced = request.args.get('announced', '') # '0', '1', or ''

    # Base query joining members with viewers to get the username
    query = '''
        SELECT m.id, m.id_viewer, v.username, m.is_announced, m.created_at, m.joined_at
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
    # Force set to 1 or toggle if not specified
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

# ==============

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

@app.route('/upetitriger', methods=['POST'])
def upeti_trigger():
    socketio.emit('trigger_upeti')
    return jsonify({"status": "success"}), 200

@app.route('/kaisars')
def kaisars_page():
    return render_template('templates/kaisars.html')

@app.route('/breaktriger', methods=['POST'])
def break_trigger():
    socketio.emit('trigger_transition')
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    listener_thread = threading.Thread(target=run_tikfinity_listener, args=(socketio,), daemon=True)
    listener_thread.start()

    message_thread = threading.Thread(target=run_message_process, daemon=True)
    message_thread.start()

    gift_thread = threading.Thread(target=run_gift_inspector, daemon=True)
    gift_thread.start()

    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
