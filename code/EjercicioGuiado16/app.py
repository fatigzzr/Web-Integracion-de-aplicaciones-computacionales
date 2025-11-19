# app.py
import os
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, Response, abort, g
from flask_cors import CORS
from google.cloud import storage
from dicttoxml import dicttoxml
from werkzeug.utils import secure_filename
import mimetypes
from flasgger import Swagger
import pymysql

# ------------------ CONFIGURATION ------------------
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
SIGNED_URL_EXPIRATION = 3600  # 1 hour

# Read from environment variables
API_TOKEN = os.getenv('API_TOKEN', 'udem')
GCS_BUCKET = os.getenv('GCS_BUCKET_NAME', 'fati_bucket')
GOOGLE_APPLICATION_CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '/home/fati/bucket/key.json')

DB_CONFIG = {
    "host": os.getenv('MYSQL_HOST', 'localhost'),
    "port": 3306,
    "user": os.getenv('MYSQL_USER', 'images_user'),
    "password": os.getenv('MYSQL_PASSWORD', '666'),
    "database": os.getenv('MYSQL_DB', 'Images'),
    "cursorclass": pymysql.cursors.DictCursor
}

# ------------------ APP INIT ------------------
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Configure CORS to allow all origins (adjust as needed for production)
CORS(app, resources={r"/*": {"origins": "*"}})

gcs_client = storage.Client.from_service_account_json(GOOGLE_APPLICATION_CREDENTIALS_PATH)
bucket = gcs_client.bucket(GCS_BUCKET)
swagger = Swagger(app)

# ------------------ DATABASE ------------------
def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(**DB_CONFIG)
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ------------------ HELPERS ------------------
def check_token():
    auth = request.headers.get('Authorization', '').strip()
    if not auth:
        abort(error_response('Missing Authorization header', 401))
    if not auth.startswith('Bearer '):
        abort(error_response('Invalid authorization scheme', 401))
    token = auth.split(' ', 1)[1].strip()
    if token != API_TOKEN:
        abort(error_response('Invalid API token', 401))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def to_response(data, root='response'):
    fmt = request.args.get('format', '').lower()
    accept = request.headers.get('Accept', '').lower()
    wants_json = fmt == 'json' or 'application/json' in accept
    if wants_json:
        return jsonify(data)
    xml = dicttoxml(data, custom_root=root, attr_type=False)
    return Response(xml, mimetype='application/xml')

def error_response(message, status_code):
    resp = to_response({'error': message}, root='error')
    resp.status_code = status_code
    return resp

def insert_metadata(name, size, mime, signed_url):
    conn = get_db()
    cur = conn.cursor()
    sql = """
    INSERT INTO images (filename, uploaded_at, size_bytes, mime_type, signed_url)
    VALUES (%s, %s, %s, %s, %s)
    """
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute(sql, (name, now, size, mime, signed_url))
    conn.commit()
    cur.close()

def generate_signed_url(blob_name, expiration=SIGNED_URL_EXPIRATION):
    blob = bucket.blob(blob_name)
    return blob.generate_signed_url(expiration=timedelta(seconds=expiration))

# ------------------ ROUTES ------------------
@app.route('/upload', methods=['POST'])
def upload():
    """
    Upload an image
    ---
    tags:
      - Images
    parameters:
      - name: file
        in: formData
        type: file
        required: true
      - name: format
        in: query
        type: string
        required: false
        description: "xml (default) or json"
    responses:
      200:
        description: Image uploaded successfully
      400:
        description: Bad request
      401:
        description: Missing or invalid token
      403:
        description: Forbidden
      413:
        description: File too large
    security:
      - Bearer: []
    """
    check_token()
    if 'file' not in request.files:
        return to_response({'error': 'no file part'}, root='error'), 400
    f = request.files['file']
    if f.filename == '':
        return to_response({'error': 'no selected file'}, root='error'), 400
    if not allowed_file(f.filename):
        return to_response({'error': 'file type not allowed'}, root='error'), 400

    filename = secure_filename(f.filename)
    blob_name = f"{int(time.time())}_{filename}"
    content = f.read()
    size = len(content)
    if size > MAX_CONTENT_LENGTH:
        return to_response({'error': 'file too large'}, root='error'), 413

    mime = f.mimetype or mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    blob = bucket.blob(blob_name)
    blob.upload_from_string(content, content_type=mime)

    signed_url = generate_signed_url(blob_name)
    insert_metadata(blob_name, size, mime, signed_url)

    resp = {
        'filename': blob_name,
        'url': signed_url,
        'uploaded_at': datetime.utcnow().isoformat() + 'Z',
        'size_bytes': size,
        'mime_type': mime
    }
    return to_response(resp)

@app.route('/images', methods=['GET'])
def images():
    """
    List all images
    ---
    tags:
      - Images
    parameters:
      - name: format
        in: query
        type: string
        required: false
        description: "xml (default) or json"
    responses:
      200:
        description: List of images
      401:
        description: Missing or invalid token
      403:
        description: Forbidden
    security:
      - Bearer: []
    """
    check_token()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, filename, uploaded_at, size_bytes, mime_type, signed_url FROM images ORDER BY uploaded_at DESC")
    rows = cur.fetchall()
    cur.close()

    items = []
    for r in rows:
        filename = r['filename']
        signed = generate_signed_url(filename)
        items.append({
            'id': r['id'],
            'filename': filename,
            'url': signed,
            'uploaded_at': r['uploaded_at'].isoformat() if isinstance(r['uploaded_at'], datetime) else str(r['uploaded_at']),
            'size_bytes': int(r['size_bytes']),
            'mime_type': r['mime_type']
        })
    return to_response({'images': items}, root='images')

# ------------------ SWAGGER ------------------
app.config['SWAGGER'] = {'title': 'Image Bucket API', 'uiversion': 3}
swagger.template = {
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Bearer token required"
        }
    }
}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
