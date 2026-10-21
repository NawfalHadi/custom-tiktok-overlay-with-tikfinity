from flask import Blueprint, jsonify, request
import json

saweria_bp = Blueprint('saweria_bp', __name__)

# Reference to socketio instance (will be attached or imported when registered)
socketio_ref = None

def init_saweria_socket(socketio_instance):
    global socketio_ref
    socketio_ref = socketio_instance

@saweria_bp.route('/api/saweria/webhook', methods=['POST'])
def handle_saweria_webhook():
    try:
        # Parse the JSON payload sent by Saweria
        data = request.get_json()
        
        if not data:
            return jsonify({"status": "error", "message": "No JSON payload found"}), 400

        print("[Saweria Webhook] Full payload:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # Extract standard fields from Saweria's webhook structure
        # (Fields typically include donor name, amount, message, etc.)
        donor_name = data.get('donator_name') or data.get('name') or 'Anonymous'
        amount = data.get('amount') or data.get('nominal') or 0
        message = data.get('message') or data.get('comment') or ''
        
        # You can log or process the donation here (e.g., save to SQLite database)
        print(f"[Saweria Webhook] Received donation from {donor_name}: Rp {amount:,} - Message: {message}")

        # Broadcast the event via Socket.IO to your frontend overlays
        if socketio_ref:
            socketio_ref.emit('saweria_donation', {
                'username': donor_name,
                'amount': amount,
                'message': message
            })

        return jsonify({"status": "success", "message": "Webhook processed successfully"}), 200

    except Exception as e:
        print(f"[Saweria Webhook Error] {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500