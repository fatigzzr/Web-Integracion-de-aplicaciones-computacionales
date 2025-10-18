# Sistema de Gestión de Libros con JWT + Redis

## Instalación

### 1. Base de Datos
```bash
mysql -u root -p < init.sql
```

### 2. Dependencias
```bash
pip install Flask Flask-SQLAlchemy Flask-JWT-Extended Flask-CORS PyMySQL redis Werkzeug
```

### 3. Ejecutar
```bash
python micro.py
```

## Pruebas

### Login
```bash
LOGIN_RESPONSE=$(curl -s -X POST http://136.115.136.5:5003/api/auth/login \
-H "Content-Type: application/json" \
-d '{"username":"usuario1","password":"12345"}')

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
```

### Obtener libros
```bash
curl -X GET http://136.115.136.5:5003/api/books \
-H "Authorization: Bearer $ACCESS_TOKEN"
```

### Agregar libro
```bash
curl -X POST http://136.115.136.5:5003/api/books \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{"title":"El Quijote","author":"Miguel de Cervantes","published_year":1605}'
```

### Logout
```bash
curl -X POST http://136.115.136.5:5003/api/auth/logout \
-H "Authorization: Bearer $ACCESS_TOKEN"
```

## Cliente Web
Abrir `index.html` en el navegador.
