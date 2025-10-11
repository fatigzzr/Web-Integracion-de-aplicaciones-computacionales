import os
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import jwt  # PyJWT

# ---------- CONFIG ----------
app = Flask(__name__)
CORS(app)

# Configuración MySQL (ajusta con variables de entorno en producción)
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'libros_user')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '666')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'Libros')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# JWT settings
JWT_SECRET = os.getenv('JWT_SECRET', 'cambia_esta_clave_secreta')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRES_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRES_MINUTES', 15))
REFRESH_TOKEN_EXPIRES_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRES_DAYS', 7))

mysql = MySQL(app)

# ---------- LOGGING ----------
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('auth_service')
# Log every incoming request (method, path, ip, body if json)
@app.before_request
def log_request_info():
    try:
        body = request.get_json(silent=True)
    except Exception:
        body = None
    logger.info("Incoming request: %s %s from %s body=%s",
                request.method, request.path, request.remote_addr, body)

# Utility: query helper
def query_db(query, args=(), one=False):
    cur = mysql.connection.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    cur = mysql.connection.cursor()
    cur.execute(query, args)
    mysql.connection.commit()
    lastrowid = cur.lastrowid
    cur.close()
    return lastrowid

# ---------- JWT helpers ----------
def create_access_token(payload: dict):
    exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
    token_payload = {**payload, "exp": exp, "type": "access"}
    token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    logger.info("Access token created for user_id=%s exp=%s", payload.get('user_id'), exp)
    return token

def create_refresh_token(payload: dict):
    exp = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRES_DAYS)
    token_payload = {**payload, "exp": exp, "type": "refresh"}
    token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    logger.info("Refresh token created for user_id=%s exp=%s", payload.get('user_id'), exp)
    return token, exp

def decode_token(token):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        logger.info("Token decoded: user_id=%s type=%s", decoded.get('user_id'), decoded.get('type'))
        return decoded
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired.")
        raise
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid token: %s", e)
        raise

# Decorator to protect routes
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            logger.warning("Authorization header missing")
            return jsonify({"msg": "Missing Authorization Header"}), 401
        parts = auth_header.split()
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            logger.warning("Authorization header malformed")
            return jsonify({"msg": "Bad Authorization header"}), 401
        token = parts[1]
        try:
            data = decode_token(token)
            if data.get('type') != 'access':
                logger.warning("Token used is not access token")
                return jsonify({"msg": "Invalid token type"}), 401
            user = query_db("SELECT id, username, email, created_at FROM users WHERE id = %s", (data['user_id'],), one=True)
            if not user:
                logger.warning("User id in token not found: %s", data.get('user_id'))
                return jsonify({"msg": "User not found"}), 404
            g.current_user = user
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"msg": "Token expired"}), 401
        except Exception as e:
            logger.exception("Token verification failed")
            return jsonify({"msg": "Invalid token"}), 401
    return decorated

# ---------- HEALTHCHECK ----------
@app.route('/api/health', methods=['GET'])
def health():
    """Simple health endpoint: checks DB connectivity and returns status."""
    db_ok = False
    try:
        cur = mysql.connection.cursor()
        cur.execute('SELECT 1')
        cur.close()
        db_ok = True
        logger.info("Health check OK: DB reachable")
    except Exception as e:
        logger.exception("Health check failed: DB not reachable")
        db_ok = False

    status = "ok" if db_ok else "error"
    return jsonify({
        "status": status,
        "db": "ok" if db_ok else "error",
        "time": datetime.utcnow().isoformat() + "Z"
    }), (200 if db_ok else 500)

# ---------- AUTH Endpoints (ahora bajo /api/auth/) ----------
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        logger.warning("Register attempt with missing fields: %s", data)
        return jsonify({"msg": "username, email and password are required"}), 400

    exists = query_db("SELECT id FROM users WHERE username = %s OR email = %s", (username, email), one=True)
    if exists:
        logger.info("Register failed - user exists username/email: %s/%s", username, email)
        return jsonify({"msg": "User with that username or email already exists"}), 409
    pw_hash = generate_password_hash(password)
    user_id = execute_db("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                         (username, email, pw_hash))
    logger.info("New user registered id=%s username=%s", user_id, username)
    return jsonify({"msg": "User created", "user_id": user_id}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    identifier = data.get('username') or data.get('email')
    password = data.get('password')

    if not identifier or not password:
        logger.warning("Login attempt missing identifier/password")
        return jsonify({"msg": "username/email and password required"}), 400

    user = query_db("SELECT id, username, email, password_hash FROM users WHERE username = %s OR email = %s",
                    (identifier, identifier), one=True)
    if not user:
        logger.info("Login failed - user not found: %s", identifier)
        return jsonify({"msg": "Invalid credentials"}), 401

    if not check_password_hash(user['password_hash'], password):
        logger.info("Login failed - wrong password for user_id=%s", user['id'])
        return jsonify({"msg": "Invalid credentials"}), 401

    payload = {"user_id": user['id']}
    access_token = create_access_token(payload)
    refresh_token, refresh_exp = create_refresh_token(payload)

    execute_db("INSERT INTO refresh_tokens (user_id, refresh_token, expires_at) VALUES (%s, %s, %s)",
               (user['id'], refresh_token, refresh_exp.strftime('%Y-%m-%d %H:%M:%S')))
    logger.info("Login success for user_id=%s - tokens issued", user['id'])

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in_minutes": ACCESS_TOKEN_EXPIRES_MINUTES
    }), 200

@app.route('/api/auth/refresh', methods=['POST'])
def refresh():
    data = request.get_json() or {}
    refresh_token = data.get('refresh_token')
    if not refresh_token:
        auth_header = request.headers.get('Authorization', '')
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            refresh_token = parts[1]

    if not refresh_token:
        logger.warning("Refresh attempted without refresh_token")
        return jsonify({"msg": "refresh_token is required"}), 400

    try:
        decoded = decode_token(refresh_token)
        if decoded.get('type') != 'refresh':
            logger.warning("Provided token to refresh is not refresh type")
            return jsonify({"msg": "Invalid token type"}), 401
        user_id = decoded['user_id']
        row = query_db("SELECT id, revoked, expires_at FROM refresh_tokens WHERE user_id = %s AND refresh_token = %s",
                       (user_id, refresh_token), one=True)
        if not row:
            logger.warning("Refresh token not found in DB for user_id=%s", user_id)
            return jsonify({"msg": "Refresh token not recognized"}), 401
        if row['revoked']:
            logger.warning("Attempt to use revoked refresh token id=%s", row['id'])
            return jsonify({"msg": "Refresh token revoked"}), 401

        access_token = create_access_token({"user_id": user_id})
        logger.info("Access token refreshed for user_id=%s", user_id)
        return jsonify({"access_token": access_token, "token_type": "bearer", "expires_in_minutes": ACCESS_TOKEN_EXPIRES_MINUTES}), 200
    except jwt.ExpiredSignatureError:
        logger.warning("Refresh token expired")
        return jsonify({"msg": "Refresh token expired"}), 401
    except Exception as e:
        logger.exception("Error processing refresh token")
        return jsonify({"msg": "Invalid refresh token"}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    data = request.get_json() or {}
    refresh_token = data.get('refresh_token')
    if not refresh_token:
        return jsonify({"msg": "refresh_token required"}), 400
    execute_db("UPDATE refresh_tokens SET revoked = 1 WHERE refresh_token = %s", (refresh_token,))
    logger.info("Logout requested - refresh token revoked")
    return jsonify({"msg": "Refresh token revoked"}), 200

# ---------- Protected API endpoints (ya bajo /api/) ----------
@app.route('/api/profile', methods=['GET'])
@login_required
def profile():
    user = g.current_user
    logger.info("Profile requested for user_id=%s", user['id'])
    return jsonify({
        "id": user['id'],
        "username": user['username'],
        "email": user['email'],
        "created_at": user['created_at'].isoformat() if isinstance(user['created_at'], datetime) else str(user['created_at'])
    }), 200

@app.route('/api/items', methods=['GET', 'POST'])
@login_required
def items():
    user = g.current_user
    if request.method == 'GET':
        rows = query_db("SELECT id, title, description, created_at FROM items WHERE user_id = %s ORDER BY created_at DESC", (user['id'],))
        logger.info("Listing %s items for user_id=%s", len(rows), user['id'])
        for r in rows:
            if isinstance(r.get('created_at'), datetime):
                r['created_at'] = r['created_at'].isoformat()
        return jsonify(rows), 200

    data = request.get_json() or {}
    title = data.get('title')
    description = data.get('description', '')
    if not title:
        logger.warning("Attempt to create item without title by user_id=%s", user['id'])
        return jsonify({"msg": "title is required"}), 400
    item_id = execute_db("INSERT INTO items (user_id, title, description) VALUES (%s, %s, %s)",
                         (user['id'], title, description))
    logger.info("Item created id=%s for user_id=%s", item_id, user['id'])
    return jsonify({"msg": "Item created", "item_id": item_id}), 201

# ---------- Run ----------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)