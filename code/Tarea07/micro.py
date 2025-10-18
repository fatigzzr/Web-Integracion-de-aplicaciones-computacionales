from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import redis

# ---------------------------------------------
# CONFIGURACIÓN INICIAL
# ---------------------------------------------
app = Flask(__name__)

# Configuración CORS para permitir peticiones desde el cliente web
CORS(app, origins=['*'], methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'], 
     allow_headers=['Content-Type', 'Authorization'])

# Base de datos MariaDB
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://books_user:666@localhost/books_tarea'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración JWT
app.config['JWT_SECRET_KEY'] = 'clave-super-secreta'  # cámbiala en producción
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=5)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=1)

# Inicializar componentes
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Conexión a Redis (para tokens y revocación)
redis_client = redis.StrictRedis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

# ---------------------------------------------
# MODELOS
# ---------------------------------------------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    created_at = db.Column(db.DateTime)

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255))
    published_year = db.Column(db.Integer)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime)

# ---------------------------------------------
# FUNCIONES JWT - REVOCACIÓN
# ---------------------------------------------
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    entry = redis_client.get(f"revoked_token:{jti}")
    return entry is not None  # True = token revocado


# ---------------------------------------------
# RUTAS DE AUTENTICACIÓN
# ---------------------------------------------
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"msg": "Credenciales inválidas"}), 401

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    # Guardar tokens en Redis con expiración
    redis_client.set(f"access_token:{access_token}", "valid", ex=300)
    redis_client.set(f"refresh_token:{refresh_token}", "valid", ex=86400)

    return jsonify(access_token=access_token, refresh_token=refresh_token)


@app.route('/api/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    redis_client.set(f"access_token:{access_token}", "valid", ex=300)
    return jsonify(access_token=access_token)


@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    redis_client.set(f"revoked_token:{jti}", "true", ex=3600)
    return jsonify(msg="Sesión cerrada correctamente"), 200


# ---------------------------------------------
# RUTAS DE LIBROS (PROTEGIDAS)
# ---------------------------------------------
@app.route('/api/books', methods=['GET'])
@jwt_required()
def get_books():
    books = Book.query.all()
    result = [
        {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "year": b.published_year
        } for b in books
    ]
    return jsonify(result)


@app.route('/api/books', methods=['POST'])
@jwt_required()
def add_book():
    data = request.get_json()
    user_id = get_jwt_identity()
    new_book = Book(
        title=data['title'],
        author=data.get('author'),
        published_year=data.get('published_year'),
        created_by=user_id
    )
    db.session.add(new_book)
    db.session.commit()
    return jsonify(msg="Libro agregado correctamente"), 201


# ---------------------------------------------
# RUTA DE PRUEBA
# ---------------------------------------------
@app.route('/')
def index():
    return jsonify(msg="API de libros con JWT + Redis funcionando"), 200


# ---------------------------------------------
# MAIN
# ---------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)

