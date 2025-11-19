# Image Bucket Microservice

Microservicio Flask para administrar imágenes almacenadas en un bucket de Google Cloud Storage (GCS). Expone rutas para subir archivos, listarlos y obtener URLs firmadas (1 hora). Responde en XML por defecto y puede devolver JSON vía `Accept: application/json` o `?format=json`. Todas las rutas requieren autenticación mediante token Bearer.

## Requisitos previos

- Python 3.10+ y `pip`
- Cuenta de servicio de GCP con acceso de lectura/escritura al bucket y archivo JSON de credenciales
- Instancia de MariaDB accesible desde la aplicación

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

Define las siguientes variables de entorno antes de ejecutar el servicio (puedes usar un archivo `.env` y `source .env`):

| Variable | Descripción |
| --- | --- |
| `API_TOKEN` | Token aceptado por el microservicio (por defecto `udem`). |
| `GCS_BUCKET_NAME` | Nombre del bucket en GCS. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Ruta absoluta al JSON de la cuenta de servicio. |
| `MYSQL_HOST` | Host de MariaDB (por defecto `localhost`). |
| `MYSQL_USER` | Usuario con permisos de lectura/escritura. |
| `MYSQL_PASSWORD` | Contraseña del usuario. |
| `MYSQL_DB` | Base de datos que contiene la tabla `images`. |

Ejemplo rápido (ajusta rutas/credenciales según tu entorno):

```bash
export API_TOKEN=udem
export GCS_BUCKET_NAME=fati_bucket
export GOOGLE_APPLICATION_CREDENTIALS=/home/fati/Microservicios/bucket/key.json
export MYSQL_HOST=localhost
export MYSQL_USER=images_user
export MYSQL_PASSWORD=666
export MYSQL_DB=Images
export FLASK_APP=app.py
```

### Base de datos

Ejecuta el script `schema.sql` en tu instancia MariaDB para crear la tabla necesaria:

```sql
SOURCE schema.sql;
```

### Ejecutar el servicio

```bash
export FLASK_APP=app.py
flask run --host=0.0.0.0 --port=5000
```

Swagger UI está disponible en `http://localhost:5000/apidocs`.

## Ejemplos de uso

> Nota: el backend responde en XML por defecto. Usa `-H "Accept: application/json"` o `?format=json` para solicitar JSON.

### Subir imagen (con autenticación)

```bash
curl -X POST http://localhost:5000/upload \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Accept: application/json" \
  -F "file=@/ruta/a/imagen.png"
```

### Subir imagen (sin token, 401)

```bash
curl -X POST http://localhost:5000/upload \
  -F "file=@/ruta/a/imagen.png"
```

### Listar imágenes (con autenticación)

```bash
curl -X GET "http://localhost:5000/images?format=json" \
  -H "Authorization: Bearer ${API_TOKEN}"
```

### Listar imágenes (sin token, 401)

```bash
curl -X GET http://localhost:5000/images
```

## Manejo de errores

Los errores comunes (token faltante, formato inválido, archivo demasiado grande, etc.) devuelven mensajes descriptivos en XML o JSON según lo solicitado junto con el código HTTP correspondiente (401, 400, 413, etc.).
