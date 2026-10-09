import threading
import logging
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO

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

@app.route('/control')
def control_panel():
    return render_template('templates/control.html')


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
