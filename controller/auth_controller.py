import random
import json
import os
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

PENDING_FILE = Path('datas') / 'pending_registrations.json'
DB_PATH = str(Path('datas') / 'viewers.db')

def init_pending_storage():
    os.makedirs('datas', exist_ok=True)
    if not PENDING_FILE.exists():
        with open(PENDING_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)

def get_pending_data():
    init_pending_storage()
    try:
        with open(PENDING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_pending_data(data):
    init_pending_storage()
    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def generate_verify_code():
    pending = get_pending_data()
    while True:
        code = f"{random.randint(100000, 999999)}"
        if code not in pending:
            return code

def create_pending_registration(email, raw_password):
    verify_code = generate_verify_code()
    pending = get_pending_data()
    
    # Hash password safely before storing
    hashed_password = generate_password_hash(raw_password)
    
    pending[verify_code] = {
        "email": email,
        "password": hashed_password,
        "verify_code": verify_code
    }
    save_pending_data(pending)
    return verify_code

def verify_code_from_tiktok(username, code_input):
    pending = get_pending_data()
    code_input = str(code_input).strip()

    if code_input not in pending:
        print(f"-> [VERIFY FAILED] Kode {code_input} tidak ditemukan.")
        return False

    user_credentials = pending[code_input]
    email = user_credentials["email"]
    hashed_password = user_credentials["password"]

    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM tb_viewers WHERE username = ?", (username,))
        viewer = cursor.fetchone()

        if viewer:
            cursor.execute("""
                UPDATE tb_viewers 
                SET email = ?, password = ?, verify_code = ?, updated_at = CURRENT_TIMESTAMP
                WHERE username = ?
            """, (email, hashed_password, code_input, username))
        else:
            cursor.execute("""
                INSERT INTO tb_viewers (username, email, password, verify_code)
                VALUES (?, ?, ?, ?)
            """, (username, email, hashed_password, code_input))

        conn.commit()

        del pending[code_input]
        save_pending_data(pending)

        print(f"-> [VERIFICATION SUCCESS] @{username} dikaitkan dengan email: {email}")
        return True

    except Exception as e:
        print(f"-> [DATABASE ERROR] Gagal verifikasi: {e}")
        return False
    finally:
        conn.close()