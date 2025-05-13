import json
import secrets
import time
import bcrypt

import globals


def hash_password(plain_password: str):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode(), salt)
    return hashed.decode()


def is_login_blocked(ip):
    if ip in globals.failed_login_attempts:
        attempts, timestamp = globals.failed_login_attempts[ip]

        if time.time() - timestamp > globals.config.login_failed_timeout:
            globals.failed_login_attempts[ip] = (0, time.time())
            return False
        return attempts >= globals.config.max_login_attempts
    return False


def record_failed_login_attempt(ip):
    current_time = time.time()
    if ip in globals.failed_login_attempts:
        attempts, timestamp = globals.failed_login_attempts[ip]

        if current_time - timestamp > globals.config.login_failed_timeout:
            globals.failed_login_attempts[ip] = (1, current_time)
        else:
            globals.failed_login_attempts[ip] = (attempts + 1, timestamp)
    else:
        globals.failed_login_attempts[ip] = (1, current_time)


def validate_session_token(token, page):
    try:
        decrypted_payload = globals.cipher_suite.decrypt(token.encode('utf-8'))
        payload = json.loads(decrypted_payload.decode('utf-8'))

        session_id = payload.get('session_id')
        if not session_id or session_id not in globals.active_sessions:
            return None

        auth_session = globals.active_sessions[session_id]

        if auth_session['page'] != page:
            return None

        if time.time() > auth_session['expiry']:
            del globals.active_sessions[session_id]
            return None

        return auth_session['user_id']
    except Exception:
        return None


def generate_session_token(user_id, page):
    session_id = secrets.token_hex(32)
    expiry = int(time.time()) + globals.config.login_session_time

    payload = {
        'session_id': session_id,
        'user_id': user_id,
        'page': page,
        'exp': expiry
    }

    payload_bytes = json.dumps(payload).encode('utf-8')
    token = globals.cipher_suite.encrypt(payload_bytes).decode('utf-8')

    globals.active_sessions[session_id] = {
        'user_id': user_id,
        'page': page,
        'expiry': expiry
    }

    return token
