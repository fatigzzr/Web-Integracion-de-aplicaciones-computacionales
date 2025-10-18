import os
import logging
import json
import hashlib
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, g, Response
from flask_cors import CORS
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
import jwt  # PyJWT
import redis

# ---------- CONFIG ----------
app = Flask(__name__)
CORS(app, 
     origins=['*'],
     allow_headers=['Content-Type', 'Authorization', 'Accept'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=True)

# Configuración MySQL (configuración directa)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'libros_user',
    'password': '666',
    'database': 'Libros',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# JWT settings
JWT_SECRET = 'cambia_esta_clave_secreta'
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRES_MINUTES = 15
REFRESH_TOKEN_EXPIRES_DAYS = 7

# Redis settings
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None

# ---------- REDIS CONNECTION ----------
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    # Test connection
    redis_client.ping()
    logger = logging.getLogger('auth_service')
    logger.info("Redis connection established successfully")
except Exception as e:
    logger = logging.getLogger('auth_service')
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None

# ---------- LOGGING ----------
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Log every incoming request (method, path, ip, body if json)
@app.before_request
def log_request_info():
    try:
        body = request.get_json(silent=True)
    except Exception:
        body = None
    logger.info("Incoming request: %s %s from %s body=%s",
                request.method, request.path, request.remote_addr, body)

# ---------- REDIS HELPERS ----------
def get_redis():
    """Get Redis client with error handling"""
    if not redis_client:
        raise Exception("Redis not available")
    return redis_client

def redis_available():
    """Check if Redis is available"""
    try:
        get_redis().ping()
        return True
    except:
        return False

def hash_token(token):
    """Create a hash of the token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()

# ---------- REDIS TOKEN MANAGEMENT ----------
def add_token_to_allowlist(token, user_id, token_type, expires_at):
    """Add token to Redis allowlist"""
    try:
        r = get_redis()
        token_hash = hash_token(token)
        key = f"allowlist:{token_hash}"
        
        token_data = {
            'user_id': user_id,
            'type': token_type,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': expires_at.isoformat()
        }
        
        # Set with expiration
        ttl = int((expires_at - datetime.utcnow()).total_seconds())
        r.setex(key, ttl, json.dumps(token_data))
        
        # Also add to user's token set for easy cleanup
        user_tokens_key = f"user_tokens:{user_id}:{token_type}"
        r.sadd(user_tokens_key, token_hash)
        r.expire(user_tokens_key, ttl)
        
        logger.info("Token added to allowlist: user_id=%s type=%s", user_id, token_type)
        return True
    except Exception as e:
        logger.error("Failed to add token to allowlist: %s", e)
        return False

def add_token_to_denylist(token, user_id=None):
    """Add token to Redis denylist"""
    try:
        r = get_redis()
        token_hash = hash_token(token)
        key = f"denylist:{token_hash}"
        
        denylist_data = {
            'user_id': user_id,
            'revoked_at': datetime.utcnow().isoformat()
        }
        
        # Set with long expiration (24 hours)
        r.setex(key, 86400, json.dumps(denylist_data))
        
        logger.info("Token added to denylist: user_id=%s", user_id)
        return True
    except Exception as e:
        logger.error("Failed to add token to denylist: %s", e)
        return False

def is_token_in_denylist(token):
    """Check if token is in denylist"""
    try:
        r = get_redis()
        token_hash = hash_token(token)
        key = f"denylist:{token_hash}"
        return r.exists(key)
    except Exception as e:
        logger.error("Failed to check denylist: %s", e)
        return False

def is_token_in_allowlist(token):
    """Check if token is in allowlist"""
    try:
        r = get_redis()
        token_hash = hash_token(token)
        key = f"allowlist:{token_hash}"
        return r.exists(key)
    except Exception as e:
        logger.error("Failed to check allowlist: %s", e)
        return False

def revoke_user_tokens(user_id, token_type=None):
    """Revoke all tokens for a user"""
    try:
        r = get_redis()
        
        if token_type:
            # Revoke specific token type
            user_tokens_key = f"user_tokens:{user_id}:{token_type}"
            token_hashes = r.smembers(user_tokens_key)
            
            for token_hash in token_hashes:
                # Move from allowlist to denylist
                allowlist_key = f"allowlist:{token_hash}"
                token_data = r.get(allowlist_key)
                if token_data:
                    r.delete(allowlist_key)
                    denylist_key = f"denylist:{token_hash}"
                    r.setex(denylist_key, 86400, token_data)
            
            r.delete(user_tokens_key)
        else:
            # Revoke all token types
            for t_type in ['access', 'refresh']:
                revoke_user_tokens(user_id, t_type)
        
        logger.info("All tokens revoked for user_id=%s", user_id)
        return True
    except Exception as e:
        logger.error("Failed to revoke user tokens: %s", e)
        return False

# ---------- RATE LIMITING ----------
def check_rate_limit(user_id, endpoint, max_requests=100, window_minutes=60):
    """Check rate limit for user/endpoint"""
    try:
        r = get_redis()
        key = f"rate_limit:{user_id}:{endpoint}"
        
        # Get current count
        current = r.get(key)
        if current is None:
            # First request in window
            r.setex(key, window_minutes * 60, 1)
            return True
        elif int(current) < max_requests:
            # Increment counter
            r.incr(key)
            return True
        else:
            # Rate limit exceeded
            return False
    except Exception as e:
        logger.error("Rate limit check failed: %s", e)
        return True  # Allow on error

def check_rate_limit_by_ip(ip, endpoint, max_requests=100, window_minutes=60):
    """Check rate limit for IP/endpoint"""
    try:
        r = get_redis()
        key = f"rate_limit_ip:{ip}:{endpoint}"
        
        # Get current count
        current = r.get(key)
        if current is None:
            # First request in window
            r.setex(key, window_minutes * 60, 1)
            return True
        elif int(current) < max_requests:
            # Increment counter
            r.incr(key)
            return True
        else:
            # Rate limit exceeded
            return False
    except Exception as e:
        logger.error("Rate limit check failed: %s", e)
        return True  # Allow request if Redis is down

# ---------- DATABASE HELPERS ----------
def query_db(query, args=(), one=False):
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, args)
            rv = cursor.fetchall()
            return (rv[0] if rv else None) if one else rv
    finally:
        connection.close()

def execute_db(query, args=()):
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, args)
            connection.commit()
            return cursor.lastrowid
    finally:
        connection.close()

# ---------- JWT HELPERS ----------
def create_access_token(payload: dict):
    exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
    token_payload = {**payload, "exp": exp, "type": "access"}
    token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    # Add to Redis allowlist
    if redis_available():
        add_token_to_allowlist(token, payload.get('user_id'), 'access', exp)
    
    logger.info("Access token created for user_id=%s exp=%s", payload.get('user_id'), exp)
    return token

def create_refresh_token(payload: dict):
    exp = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRES_DAYS)
    token_payload = {**payload, "exp": exp, "type": "refresh"}
    token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    # Add to Redis allowlist
    if redis_available():
        add_token_to_allowlist(token, payload.get('user_id'), 'refresh', exp)
    
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

# ---------- AUTHENTICATION DECORATOR ----------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check rate limit (using IP as identifier) - TEMPORARILY DISABLED FOR TESTING
        # if redis_available():
        #     client_ip = request.remote_addr
        #     # Use IP-based rate limiting for unauthenticated requests
        #     if not check_rate_limit_by_ip(client_ip, 'auth', max_requests=50, window_minutes=15):
        #         logger.warning("Rate limit exceeded for IP: %s", client_ip)
        #         return jsonify({"msg": "Rate limit exceeded"}), 429
        
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
            logger.info("🔍 Validating token for endpoint: %s", request.endpoint)
            
            # Check if token is in denylist (Redis)
            if redis_available() and is_token_in_denylist(token):
                logger.warning("Token found in denylist")
                return jsonify({"msg": "Token has been revoked"}), 401
            
            # Check if token is in allowlist (Redis) - optional extra security
            # Note: Allowlist check is optional for backward compatibility
            # if redis_available() and not is_token_in_allowlist(token):
            #     logger.warning("Token not found in allowlist")
            #     return jsonify({"msg": "Token not recognized"}), 401
            
            data = decode_token(token)
            logger.info("✅ Token decoded successfully: user_id=%s type=%s", data.get('user_id'), data.get('type'))
            
            if data.get('type') != 'access':
                logger.warning("Token used is not access token")
                return jsonify({"msg": "Invalid token type"}), 401
            
            user = query_db("SELECT id, username, email, created_at FROM users WHERE id = %s", (data['user_id'],), one=True)
            if not user:
                logger.warning("User id in token not found: %s", data.get('user_id'))
                return jsonify({"msg": "User not found"}), 404
            
            logger.info("✅ User found: %s", user.get('username'))
            g.current_user = user
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"msg": "Token expired"}), 401
        except Exception as e:
            logger.exception("Token verification failed")
            return jsonify({"msg": "Invalid token"}), 401
    return decorated

# ---------- CORS HANDLER ----------
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization,Accept")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        return response

# ---------- HEALTHCHECK ----------
@app.route('/api/health', methods=['GET'])
def health():
    """Enhanced health endpoint: checks DB and Redis connectivity"""
    db_ok = False
    redis_ok = False
    
    # Check MySQL
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        connection.close()
        db_ok = True
        logger.info("Health check OK: DB reachable")
    except Exception as e:
        logger.exception("Health check failed: DB not reachable")
        db_ok = False
    
    # Check Redis
    if redis_available():
        try:
            get_redis().ping()
            redis_ok = True
            logger.info("Health check OK: Redis reachable")
        except Exception as e:
            logger.exception("Health check failed: Redis not reachable")
            redis_ok = False
    else:
        redis_ok = False
        logger.warning("Redis not configured")

    status = "ok" if (db_ok and redis_ok) else "degraded" if db_ok else "error"
    return jsonify({
        "status": status,
        "db": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
        "time": datetime.utcnow().isoformat() + "Z"
    }), (200 if db_ok else 500)

# ---------- AUTH ENDPOINTS ----------
@app.route('/api/auth/register', methods=['POST'])
def register():
    # Rate limiting
    if redis_available():
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip, 'register', max_requests=5, window_minutes=60):
            return jsonify({"msg": "Registration rate limit exceeded"}), 429
    
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
    # Rate limiting
    if redis_available():
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip, 'login', max_requests=10, window_minutes=15):
            return jsonify({"msg": "Login rate limit exceeded"}), 429
    
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

    # Revoke any existing tokens for this user
    if redis_available():
        revoke_user_tokens(user['id'])

    payload = {"user_id": user['id']}
    access_token = create_access_token(payload)
    refresh_token, refresh_exp = create_refresh_token(payload)

    # Add tokens to Redis allowlist
    if redis_available():
        access_exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
        add_token_to_allowlist(access_token, user['id'], 'access', access_exp)
        add_token_to_allowlist(refresh_token, user['id'], 'refresh', refresh_exp)
        logger.info("Tokens added to allowlist for user_id=%s", user['id'])

    # Store refresh token in MySQL (for backward compatibility)
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
    # Rate limiting
    if redis_available():
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip, 'refresh', max_requests=20, window_minutes=15):
            return jsonify({"msg": "Refresh rate limit exceeded"}), 429
    
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
        # Check if refresh token is in denylist
        if redis_available() and is_token_in_denylist(refresh_token):
            logger.warning("Refresh token found in denylist")
            return jsonify({"msg": "Refresh token has been revoked"}), 401
        
        decoded = decode_token(refresh_token)
        if decoded.get('type') != 'refresh':
            logger.warning("Provided token to refresh is not refresh type")
            return jsonify({"msg": "Invalid token type"}), 401
        
        user_id = decoded['user_id']
        
        # Check in MySQL for backward compatibility
        row = query_db("SELECT id, revoked, expires_at FROM refresh_tokens WHERE user_id = %s AND refresh_token = %s",
                       (user_id, refresh_token), one=True)
        if not row:
            logger.warning("Refresh token not found in DB for user_id=%s", user_id)
            return jsonify({"msg": "Refresh token not recognized"}), 401
        if row['revoked']:
            logger.warning("Attempt to use revoked refresh token id=%s", row['id'])
            return jsonify({"msg": "Refresh token revoked"}), 401

        # Create new access token
        access_token = create_access_token({"user_id": user_id})
        
        # Add new access token to Redis allowlist
        if redis_available():
            access_exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
            add_token_to_allowlist(access_token, user_id, 'access', access_exp)
            logger.info("New access token added to allowlist for user_id=%s", user_id)
        
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
    access_token = data.get('access_token')
    
    if not refresh_token and not access_token:
        return jsonify({"msg": "refresh_token or access_token required"}), 400

    try:
        # Add tokens to denylist
        if redis_available():
            if access_token:
                # Decode to get user_id
                try:
                    decoded = decode_token(access_token)
                    user_id = decoded.get('user_id')
                    add_token_to_denylist(access_token, user_id)
                except:
                    pass  # Token might be invalid, but we still want to denylist it
            
            if refresh_token:
                # Try to get user_id from refresh token
                try:
                    decoded = decode_token(refresh_token)
                    user_id = decoded.get('user_id')
                    add_token_to_denylist(refresh_token, user_id)
                except:
                    pass
        
        # Also revoke in MySQL for backward compatibility
        if refresh_token:
            execute_db("UPDATE refresh_tokens SET revoked = 1 WHERE refresh_token = %s", (refresh_token,))
        
        logger.info("Logout requested - tokens revoked")
        return jsonify({"msg": "Tokens revoked successfully"}), 200
    except Exception as e:
        logger.exception("Error during logout")
        return jsonify({"msg": "Logout failed"}), 500

@app.route('/api/auth/revoke-all', methods=['POST'])
@login_required
def revoke_all_tokens():
    """Revoke all tokens for the current user"""
    user = g.current_user
    
    try:
        if redis_available():
            revoke_user_tokens(user['id'])
        
        # Also revoke in MySQL
        execute_db("UPDATE refresh_tokens SET revoked = 1 WHERE user_id = %s", (user['id'],))
        
        logger.info("All tokens revoked for user_id=%s", user['id'])
        return jsonify({"msg": "All tokens revoked successfully"}), 200
    except Exception as e:
        logger.exception("Error revoking all tokens")
        return jsonify({"msg": "Failed to revoke tokens"}), 500

# ---------- PROTECTED API ENDPOINTS (BOOKS) ----------
import xml.etree.ElementTree as ET

def dict_to_xml_book(row):
    book = ET.Element("book", isbn=row['isbn'])
    ET.SubElement(book, "title").text = row['title']
    ET.SubElement(book, "author").text = row['author_names']
    ET.SubElement(book, "publication_year").text = str(row['publication_year'])
    ET.SubElement(book, "genre").text = row['genre']
    ET.SubElement(book, "price").text = str(row['price'])
    ET.SubElement(book, "stock").text = str(row['stock']).lower()
    ET.SubElement(book, "format").text = row['format']
    return book

def query_books(sql, params=None):
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            rows = cursor.fetchall()
            return rows
    finally:
        connection.close()

def books_to_xml(books):
    library = ET.Element("library")
    for b in books:
        library.append(dict_to_xml_book(b))
    return ET.tostring(library, encoding="utf-8", xml_declaration=True)

@app.route("/api/books", methods=["GET"])
@login_required
def get_all_books():
    """GET /api/books → muestra todos los libros en formato XML"""
    sql = """
        SELECT b.*, g.name AS genre, f.name AS format,
        GROUP_CONCAT(a.name SEPARATOR ', ') AS author_names
        FROM Book b
        LEFT JOIN Genre g ON b.genre_id = g.genre_id
        LEFT JOIN Format f ON b.format_id = f.format_id
        LEFT JOIN BookAuthor ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        GROUP BY b.book_id
    """
    books = query_books(sql)
    return Response(books_to_xml(books), mimetype="application/xml")

@app.route("/api/books/<isbn>", methods=["GET"])
@login_required
def get_book_by_isbn(isbn):
    """GET /api/books/ISBN → muestra un libro si se manda el ISBN"""
    sql = """
        SELECT b.*, g.name AS genre, f.name AS format,
        GROUP_CONCAT(a.name SEPARATOR ', ') AS author_names
        FROM Book b
        LEFT JOIN Genre g ON b.genre_id = g.genre_id
        LEFT JOIN Format f ON b.format_id = f.format_id
        LEFT JOIN BookAuthor ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE b.isbn=%s
        GROUP BY b.book_id
    """
    books = query_books(sql, (isbn,))
    return Response(books_to_xml(books), mimetype="application/xml")

@app.route("/api/books/format/<format_name>", methods=["GET"])
@login_required
def get_books_by_format(format_name):
    """GET /api/books/format/digital → muestra todos los libros con el formato digital"""
    sql = """
        SELECT b.*, g.name AS genre, f.name AS format,
        GROUP_CONCAT(a.name SEPARATOR ', ') AS author_names
        FROM Book b
        LEFT JOIN Genre g ON b.genre_id = g.genre_id
        LEFT JOIN Format f ON b.format_id = f.format_id
        LEFT JOIN BookAuthor ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE f.name=%s
        GROUP BY b.book_id
    """
    books = query_books(sql, (format_name,))
    return Response(books_to_xml(books), mimetype="application/xml")

@app.route("/api/books/author/<author_name>", methods=["GET"])
@login_required
def get_books_by_author(author_name):
    """GET /api/books/author/ → muestra todos los libros de un autor"""
    sql = """
        SELECT b.*, g.name AS genre, f.name AS format,
        GROUP_CONCAT(a.name SEPARATOR ', ') AS author_names
        FROM Book b
        LEFT JOIN Genre g ON b.genre_id = g.genre_id
        LEFT JOIN Format f ON b.format_id = f.format_id
        LEFT JOIN BookAuthor ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE a.name LIKE %s
        GROUP BY b.book_id
    """
    books = query_books(sql, ("%" + author_name + "%",))
    return Response(books_to_xml(books), mimetype="application/xml")

@app.route("/api/books/insert", methods=["POST"])
@login_required
def insert_book():
    """POST /api/books/insert → inserta un nuevo libro"""
    logger.info("📚 Insert book endpoint called - Headers: %s", dict(request.headers))
    
    # Get user from decorator validation
    user = g.current_user
    logger.info("✅ User authenticated: %s", user.get('username'))
    
    # Now process the XML data
    data = request.data
    root = ET.fromstring(data)
    
    isbn = root.attrib['isbn']
    title = root.find("title").text
    authors = [a.strip() for a in root.find("author").text.split(",")]
    pub_year = int(root.find("publication_year").text)
    genre = root.find("genre").text
    price = float(root.find("price").text)
    stock = root.find("stock").text.lower() == "true"
    fmt = root.find("format").text
    
    logger.info("📚 Processing book: ISBN=%s, Title=%s, Genre=%s, Format=%s", isbn, title, genre, fmt)
    
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            # Insert Genre
            logger.info("🔍 Inserting genre: %s", genre)
            cursor.execute("INSERT INTO Genre(name) VALUES(%s) ON DUPLICATE KEY UPDATE name=name", (genre,))
            cursor.execute("SELECT genre_id FROM Genre WHERE name=%s", (genre,))
            genre_result = cursor.fetchone()
            logger.info("🔍 Genre result: %s", genre_result)
            if not genre_result:
                raise ValueError(f"Failed to create or find genre '{genre}'")
            genre_id = genre_result[0]
            logger.info("✅ Genre ID: %s", genre_id)
            
            # Insert Format
            cursor.execute("INSERT INTO Format(name) VALUES(%s) ON DUPLICATE KEY UPDATE name=name", (fmt,))
            cursor.execute("SELECT format_id FROM Format WHERE name=%s", (fmt,))
            format_result = cursor.fetchone()
            if not format_result:
                raise ValueError(f"Failed to create or find format '{fmt}'")
            format_id = format_result[0]
            
            # Insert Book
            cursor.execute("""
                INSERT INTO Book(isbn, title, publication_year, price, stock, genre_id, format_id)
                VALUES(%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE title=VALUES(title), publication_year=VALUES(publication_year),
                price=VALUES(price), stock=VALUES(stock), genre_id=VALUES(genre_id), format_id=VALUES(format_id)
            """, (isbn, title, pub_year, price, stock, genre_id, format_id))
            
            # Book ID
            cursor.execute("SELECT book_id FROM Book WHERE isbn=%s", (isbn,))
            book_result = cursor.fetchone()
            if not book_result:
                raise ValueError(f"Failed to create or find book with ISBN '{isbn}'")
            book_id = book_result[0]
            
            # Insert Authors
            for a in authors:
                cursor.execute("INSERT INTO Author(name) VALUES(%s) ON DUPLICATE KEY UPDATE name=name", (a,))
                cursor.execute("SELECT author_id FROM Author WHERE name=%s", (a,))
                author_result = cursor.fetchone()
                if not author_result:
                    raise ValueError(f"Failed to create or find author '{a}'")
                author_id = author_result[0]
                # Insert into BookAuthor
                cursor.execute("INSERT IGNORE INTO BookAuthor(book_id, author_id) VALUES(%s,%s)", (book_id, author_id))
            
            connection.commit()
    except ValueError as e:
        logger.warning("Validation error inserting book: %s", str(e))
        response = ET.Element("response")
        ET.SubElement(response, "status").text = "error"
        ET.SubElement(response, "message").text = str(e)
        return Response(ET.tostring(response, encoding="utf-8", xml_declaration=True), mimetype="application/xml"), 400
    except Exception as e:
        logger.exception("Unexpected error inserting book: %s", str(e))
        response = ET.Element("response")
        ET.SubElement(response, "status").text = "error"
        ET.SubElement(response, "message").text = f"Database error: {str(e)}"
        return Response(ET.tostring(response, encoding="utf-8", xml_declaration=True), mimetype="application/xml"), 500
    finally:
        connection.close()
    
    response = ET.Element("response")
    ET.SubElement(response, "status").text = "success"
    return Response(ET.tostring(response, encoding="utf-8", xml_declaration=True), mimetype="application/xml")

@app.route("/api/books/update", methods=["POST"])
@login_required
def update_book():
    """POST /api/books/update → actualiza un libro"""
    return insert_book()  # misma lógica de insert ya maneja ON DUPLICATE KEY UPDATE

@app.route("/api/books/delete", methods=["POST"])
@login_required
def delete_books():
    """POST /api/books/delete → elimina libros por ISBN"""
    # Get user from decorator validation
    user = g.current_user
    logger.info("✅ User authenticated for delete: %s", user.get('username'))
    
    # Now process the XML data
    data = request.data
    root = ET.fromstring(data)
    isbns = [i.text for i in root.findall("isbn")]
    
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            for isbn in isbns:
                # Obtener book_id
                cursor.execute("SELECT book_id FROM Book WHERE isbn=%s", (isbn,))
                res = cursor.fetchone()
                if res:
                    book_id = res[0]
                    cursor.execute("DELETE FROM BookAuthor WHERE book_id=%s", (book_id,))
                    cursor.execute("DELETE FROM Book WHERE book_id=%s", (book_id,))
            
            connection.commit()
    finally:
        connection.close()
    
    response = ET.Element("response")
    ET.SubElement(response, "status").text = "deleted"
    return Response(ET.tostring(response, encoding="utf-8", xml_declaration=True), mimetype="application/xml")

@app.route("/api/formats", methods=["GET"])
@login_required
def get_formats():
    """GET /api/formats → obtiene los formatos disponibles"""
    sql = "SELECT format_id, name FROM Format"
    formats = query_books(sql)
    root = ET.Element("formats")
    for f in formats:
        f_el = ET.SubElement(root, "format")
        ET.SubElement(f_el, "id").text = str(f["format_id"])
        ET.SubElement(f_el, "name").text = f["name"]
    return Response(ET.tostring(root), mimetype="application/xml")

@app.route("/api/genres", methods=["GET"])
@login_required
def get_genres():
    """GET /api/genres → obtiene los géneros disponibles"""
    sql = "SELECT genre_id, name FROM Genre"
    genres = query_books(sql)
    root = ET.Element("genres")
    for g in genres:
        g_el = ET.SubElement(root, "genre")
        ET.SubElement(g_el, "id").text = str(g["genre_id"])
        ET.SubElement(g_el, "name").text = g["name"]
    return Response(ET.tostring(root), mimetype="application/xml")

# ---------- ADMIN ENDPOINTS ----------
@app.route('/api/admin/redis-status', methods=['GET'])
@login_required
def redis_status():
    """Check Redis status and statistics"""
    user = g.current_user
    
    # Simple admin check (you might want to implement proper admin roles)
    if user['id'] != 1:  # Assuming user_id 1 is admin
        return jsonify({"msg": "Admin access required"}), 403
    
    try:
        r = get_redis()
        info = r.info()
        
        return jsonify({
            "redis_connected": True,
            "redis_version": info.get('redis_version'),
            "used_memory": info.get('used_memory_human'),
            "connected_clients": info.get('connected_clients'),
            "total_commands_processed": info.get('total_commands_processed')
        }), 200
    except Exception as e:
        return jsonify({
            "redis_connected": False,
            "error": str(e)
        }), 500

@app.route('/api/admin/clear-rate-limits', methods=['POST'])
def clear_rate_limits():
    """Clear all rate limit keys from Redis"""
    if not redis_available():
        return jsonify({"msg": "Redis not available"}), 503
    
    try:
        r = get_redis()
        # Clear all rate limit keys
        keys = r.keys("rate_limit*")
        if keys:
            r.delete(*keys)
            return jsonify({"msg": f"Cleared {len(keys)} rate limit keys"})
        else:
            return jsonify({"msg": "No rate limit keys found"})
    except Exception as e:
        return jsonify({"msg": f"Error clearing rate limits: {str(e)}"}), 500

# ---------- RUN ----------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)