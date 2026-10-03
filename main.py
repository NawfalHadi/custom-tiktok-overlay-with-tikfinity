import threading
from flask import Flask, request, jsonify,render_template
from flask_socketio import SocketIO
from listener import run_tikfinity_listener


app = Flask(__name__, template_folder='.')
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/control')
def control_panel():
    return render_template('templates/control.html')

@app.route('/comments-overlay')
def comments_overlay():
    return render_template('templates/comments.html')

@app.route('/transition')
def transition_overlay():
    return render_template('templates/transition.html')

@app.route('/breaktriger', methods=['POST'])
def break_trigger():
    socketio.emit('trigger_transition')
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    listener_thread = threading.Thread(target=run_tikfinity_listener, args=(socketio,), daemon=True)
    listener_thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)