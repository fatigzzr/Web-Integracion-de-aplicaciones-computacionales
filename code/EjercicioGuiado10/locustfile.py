"""
Locust Load Testing Script para Microservicio de Libros
Pruebas de estrés para todos los endpoints del microservicio
"""

from locust import HttpUser, task, between, events
import random
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import threading

# Configuración del servidor
HOST = "http://34.72.192.189:5003"

# Datos de prueba
TEST_ISBNS = [
    "978-0-124761-28-5",
    "978-0-14-028333-4",
    "978-0-208629-13-7",
    "978-0-242176-54-9",
    "978-0-273660-38-6",
    "978-0-308563-81-3",
    "978-0-308704-85-3",
    "978-0-313628-30-3",
    "978-0-316-76948-0",
    "978-0-316-76949-7",
    "978-0-316-76950-3",
    "978-0-316-76951-0",
    "978-0-316-76952-7",
    "978-0-316-76953-4",
    "978-0-316-76954-1",
    "978-0-316-76955-8",
    "978-0-316-76956-5",
    "978-0-316-76957-2",
    "978-0-316-76958-9",
    "978-0-316-76959-6",
    "978-0-316-76960-2",
    "978-0-359144-72-4",
    "978-0-359666-38-1",
    "978-0-364208-93-4",
    "978-0-398373-98-1",
    "978-0-421446-51-4",
    "978-0-477235-12-3",
    "978-0-496781-40-0",
    "978-0-579395-87-7",
    "978-0-618-34614-4",
    "978-0-679-72369-5",
    "978-0-704876-80-9",
    "978-0-742760-28-6",
    "978-0-7432-4722-1",
    "978-0-7475-3269-9",
    "978-0-7475-3274-3",
    "978-0-7475-4624-5",
    "978-0-857318-80-3",
    "978-0-864544-17-8",
    "978-0-880743-23-5",
    "978-0-922461-44-8",
    "978-0-928572-85-3",
    "978-0-986378-12-6",
    "978-0-999999-99-9"
]

TEST_FORMATS = [
    "audiolibro",
    "Box Set",
    "digital",
    "físico",
    "Hardcover",
    "Paperback"
]
TEST_GENRES = [
    "Biografía",
    "Ciencia Ficción",
    "Classic",
    "Dystopian",
    "Fantasy",
    "Historia",
    "Non-fiction",
    "Novela",
    "Novela Clásica",
    "Terror",
    "Young Adult"
]
TEST_AUTHORS = [
    "J.K. Rowling",
    "J.R.R. Tolkien",
    "F. Scott Fitzgerald",
    "George Orwell",
    "Harper Lee",
    "John Green",
    "David Levithan",
    "Maureen Johnson",
    "Lauren Myracle",
    "Suzanne Collins",
    "Stephenie Meyer",
    "Miguel de Cervantes",
    "Miguel de Cervantes Saavedra",
    "Jorge Luis Borges",
    "Gabriel García Márquez",
    "Isabel Allende"
]

# Lista de usuarios de prueba para pruebas de carga
# Cada usuario virtual de Locust usará un usuario diferente
# IMPORTANTE: Estos usuarios deben existir en la base de datos antes de ejecutar las pruebas
# Puedes crearlos manualmente o usar la tarea register_user durante las pruebas
TEST_USERS = [
    {"username": "desktop@gmail.com", "password": "desktop"},
    {"username": "user1@test.com", "password": "testpass123"},
    {"username": "user2@test.com", "password": "testpass123"},
    {"username": "user3@test.com", "password": "testpass123"},
    {"username": "user4@test.com", "password": "testpass123"},
    {"username": "user5@test.com", "password": "testpass123"},
    {"username": "user6@test.com", "password": "testpass123"},
    {"username": "user7@test.com", "password": "testpass123"},
    {"username": "user8@test.com", "password": "testpass123"},
    {"username": "user9@test.com", "password": "testpass123"},
    {"username": "user10@test.com", "password": "testpass123"},
    {"username": "user11@test.com", "password": "testpass123"},
    {"username": "user12@test.com", "password": "testpass123"},
    {"username": "user13@test.com", "password": "testpass123"},
    {"username": "user14@test.com", "password": "testpass123"},
    {"username": "user15@test.com", "password": "testpass123"},
    {"username": "user16@test.com", "password": "testpass123"},
    {"username": "user17@test.com", "password": "testpass123"},
    {"username": "user18@test.com", "password": "testpass123"},
    {"username": "user19@test.com", "password": "testpass123"},
    {"username": "user20@test.com", "password": "testpass123"},
    {"username": "user21@test.com", "password": "testpass123"},
    {"username": "user22@test.com", "password": "testpass123"},
    {"username": "user23@test.com", "password": "testpass123"},
    {"username": "user24@test.com", "password": "testpass123"},
    {"username": "user25@test.com", "password": "testpass123"},
    {"username": "user26@test.com", "password": "testpass123"},
    {"username": "user27@test.com", "password": "testpass123"},
    {"username": "user28@test.com", "password": "testpass123"},
    {"username": "user29@test.com", "password": "testpass123"},
    {"username": "user30@test.com", "password": "testpass123"},
    {"username": "user31@test.com", "password": "testpass123"},
    {"username": "user32@test.com", "password": "testpass123"},
    {"username": "user33@test.com", "password": "testpass123"},
    {"username": "user34@test.com", "password": "testpass123"},
    {"username": "user35@test.com", "password": "testpass123"},
    {"username": "user36@test.com", "password": "testpass123"},
    {"username": "user37@test.com", "password": "testpass123"},
    {"username": "user38@test.com", "password": "testpass123"},
    {"username": "user39@test.com", "password": "testpass123"},
    {"username": "user40@test.com", "password": "testpass123"},
    {"username": "user41@test.com", "password": "testpass123"},
    {"username": "user42@test.com", "password": "testpass123"},
    {"username": "user43@test.com", "password": "testpass123"},
    {"username": "user44@test.com", "password": "testpass123"},
    {"username": "user45@test.com", "password": "testpass123"},
    {"username": "user46@test.com", "password": "testpass123"},
    {"username": "user47@test.com", "password": "testpass123"},
    {"username": "user48@test.com", "password": "testpass123"},
    {"username": "user49@test.com", "password": "testpass123"},
    {"username": "user50@test.com", "password": "testpass123"},
]

# Contador global para asignar usuarios de forma round-robin
_user_counter = 0
_user_lock = threading.Lock()

def get_next_user():
    """Obtiene el siguiente usuario de la lista de forma thread-safe"""
    global _user_counter
    with _user_lock:
        user = TEST_USERS[_user_counter % len(TEST_USERS)]
        _user_counter += 1
        return user


class MicroserviceUser(HttpUser):
    """
    Usuario simulado que realiza peticiones al microservicio
    """
    wait_time = between(3, 8)  # Espera entre 3 y 8 segundos entre peticiones (reducir rate limiting)
    
    def on_start(self):
        """
        Se ejecuta cuando un usuario inicia la sesión
        Realiza login para obtener el token de autenticación
        Cada usuario virtual de Locust usará un usuario diferente de TEST_USERS
        """
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        
        # Asignar un usuario diferente a cada usuario virtual de Locust
        # Esto evita que múltiples usuarios virtuales compartan el mismo usuario real
        # y que un revoke_all_tokens afecte a otros usuarios
        user_credentials = get_next_user()
        self.username = user_credentials["username"]
        
        login_data = {
            "username": user_credentials["username"],
            "password": user_credentials["password"]
        }
        
        with self.client.post(
            "/api/auth/login",
            json=login_data,
            catch_response=True,
            name="Login (on_start)"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                self.user_id = data.get("user_id")
                response.success()
            elif response.status_code == 429:
                # Rate limit - marcar como fallo para estadísticas
                response.failure("Rate limit exceeded (429)")
            elif response.status_code == 401:
                # Credenciales inválidas - el usuario no existe, intentar registrarlo
                response.failure(f"Login failed: User {user_credentials['username']} not found. Try registering first.")
            else:
                response.failure(f"Login failed: {response.status_code}")
                # Si el login falla, el usuario no podrá hacer peticiones autenticadas
    
    def get_auth_headers(self):
        """Retorna headers con autenticación"""
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def _try_refresh_token(self):
        """Intenta refrescar el access token usando el refresh token"""
        if not self.refresh_token:
            return False
        
        try:
            with self.client.post(
                "/api/auth/refresh",
                json={"refresh_token": self.refresh_token},
                catch_response=True,
                name="Refresh Token (auto)"
            ) as response:
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    response.success()
                    return True
                elif response.status_code == 401:
                    # Refresh token expirado o inválido, limpiar
                    self.access_token = None
                    self.refresh_token = None
                    response.failure("Refresh token expired")
                    return False
                elif response.status_code == 429:
                    # Rate limit - no limpiar tokens, solo marcar como fallo
                    # El token sigue siendo válido, solo hay que esperar
                    response.failure("Rate limit exceeded (429)")
                    return False
                else:
                    # Otros errores (500, etc.)
                    response.failure(f"Refresh failed: {response.status_code}")
                    return False
        except Exception as e:
            # Error de conexión u otro error
            return False
    
    def _ensure_valid_token(self):
        """Asegura que tenemos un token válido, refrescando si es necesario"""
        if self.access_token:
            return True
        
        # Solo intentar refrescar si tenemos refresh_token
        # No intentar si ya sabemos que está expirado (evitar intentos repetidos)
        if self.refresh_token:
            return self._try_refresh_token()
        
        # Si no hay refresh token, necesitamos hacer login
        # Pero no lo hacemos aquí para evitar rate limiting
        return False
    
    # ========== ENDPOINTS PÚBLICOS ==========
    
    @task(10)
    def health_check(self):
        """GET /api/health - Health check (sin autenticación)"""
        self.client.get("/api/health", name="Health Check")
    
    @task(1)  # Muy bajo para evitar rate limiting (5 requests/hora por IP)
    def register_user(self):
        """POST /api/auth/register - Registrar nuevo usuario"""
        # Generar datos únicos para evitar conflictos
        username = f"testuser_{random.randint(1000000, 9999999)}"  # Rango más amplio
        email = f"{username}@test.com"
        password = "testpass123"
        
        with self.client.post(
            "/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password
            },
            catch_response=True,
            name="Register User"
        ) as response:
            if response.status_code in [201, 409]:  # 409 = usuario ya existe
                response.success()
            elif response.status_code == 429:
                # Rate limit - marcar como fallo para estadísticas
                response.failure("Rate limit exceeded (429)")
            else:
                response.failure(f"Register failed: {response.status_code}")
    
    # ========== ENDPOINTS DE AUTENTICACIÓN ==========
    
    @task(3)  # Moderado - solo si no tenemos token (límite: 10/15min por IP)
    def login(self):
        """POST /api/auth/login - Login"""
        # Solo intentar login si no tenemos token o si el token expiró
        if self.access_token:
            return  # Ya tenemos token, no necesitamos hacer login de nuevo
        
        # Usar el mismo usuario asignado en on_start
        if not hasattr(self, 'username'):
            # Si no tenemos username asignado, usar el primero de la lista
            user_credentials = TEST_USERS[0]
        else:
            # Buscar las credenciales del usuario asignado
            user_credentials = next((u for u in TEST_USERS if u["username"] == self.username), TEST_USERS[0])
        
        login_data = {
            "username": user_credentials["username"],
            "password": user_credentials["password"]
        }
        
        with self.client.post(
            "/api/auth/login",
            json=login_data,
            catch_response=True,
            name="Login"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                response.success()
            elif response.status_code == 429:
                # Rate limit - marcar como fallo para estadísticas
                response.failure("Rate limit exceeded (429)")
            else:
                response.failure(f"Login failed: {response.status_code}")
    
    @task(5)  # Aumentado para refrescar tokens más frecuentemente
    def refresh_token(self):
        """POST /api/auth/refresh - Refrescar access token"""
        if not self.refresh_token:
            return
        
        with self.client.post(
            "/api/auth/refresh",
            json={"refresh_token": self.refresh_token},
            catch_response=True,
            name="Refresh Token"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                response.success()
            elif response.status_code == 429:
                # Rate limit - marcar como fallo para estadísticas
                response.failure("Rate limit exceeded (429)")
            elif response.status_code == 401:
                # Token expirado o inválido, limpiar tokens
                self.access_token = None
                self.refresh_token = None
                response.failure("Refresh token expired")
            else:
                response.failure(f"Refresh failed: {response.status_code}")
    
    @task(1)
    def logout(self):
        """POST /api/auth/logout - Logout"""
        if not self.access_token:
            return
        
        with self.client.post(
            "/api/auth/logout",
            json={
                "access_token": self.access_token,
                "refresh_token": self.refresh_token
            },
            catch_response=True,
            name="Logout"
        ) as response:
            if response.status_code == 200:
                response.success()
                # Limpiar tokens después del logout
                self.access_token = None
                self.refresh_token = None
            else:
                response.failure(f"Logout failed: {response.status_code}")
    
    # ========== ENDPOINTS DE LIBROS (REQUIEREN AUTH) ==========
    
    @task(15)
    def get_all_books(self):
        """GET /api/books - Obtener todos los libros"""
        if not self.access_token:
            # Intentar refrescar token si tenemos refresh_token
            if not self._ensure_valid_token():
                return
        
        with self.client.get(
            "/api/books",
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Get All Books"
        ) as response:
            if response.status_code == 401:
                # Token expirado, intentar refrescar
                self.access_token = None
                if self._try_refresh_token():
                    # Reintentar con nuevo token
                    retry_response = self.client.get(
                        "/api/books",
                        headers=self.get_auth_headers(),
                        name="Get All Books (retry)"
                    )
                    if retry_response.status_code == 200:
                        response.success()
                    else:
                        response.failure("Token expired (retry failed)")
                else:
                    response.failure("Token expired")
            elif response.status_code != 200:
                response.failure(f"Request failed: {response.status_code}")
            else:
                response.success()
    
    @task(10)
    def get_book_by_isbn(self):
        """GET /api/books/<isbn> - Obtener libro por ISBN"""
        if not self.access_token:
            if not self._ensure_valid_token():
                return
        
        isbn = random.choice(TEST_ISBNS)
        with self.client.get(
            f"/api/books/{isbn}",
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Get Book by ISBN"
        ) as response:
            if response.status_code == 401:
                self.access_token = None
                if self._try_refresh_token():
                    response.success()  # Token refrescado, considerar éxito
                    return
                response.failure("Token expired")
            elif response.status_code != 200:
                response.failure(f"Request failed: {response.status_code}")
            else:
                response.success()
    
    @task(8)
    def get_books_by_format(self):
        """GET /api/books/format/<format_name> - Obtener libros por formato"""
        if not self.access_token:
            if not self._ensure_valid_token():
                return
        
        format_name = random.choice(TEST_FORMATS)
        with self.client.get(
            f"/api/books/format/{format_name}",
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Get Books by Format"
        ) as response:
            if response.status_code == 401:
                self.access_token = None
                if self._try_refresh_token():
                    response.success()
                    return
                response.failure("Token expired")
            elif response.status_code != 200:
                response.failure(f"Request failed: {response.status_code}")
            else:
                response.success()
    
    @task(8)
    def get_books_by_author(self):
        """GET /api/books/author/<author_name> - Obtener libros por autor"""
        if not self.access_token:
            if not self._ensure_valid_token():
                return
        
        author_name = random.choice(TEST_AUTHORS)
        with self.client.get(
            f"/api/books/author/{author_name}",
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Get Books by Author"
        ) as response:
            if response.status_code == 401:
                self.access_token = None
                if self._try_refresh_token():
                    response.success()
                    return
                response.failure("Token expired")
            elif response.status_code != 200:
                response.failure(f"Request failed: {response.status_code}")
            else:
                response.success()
    
    @task(5)
    def insert_book(self):
        """PUT /api/books/insert - Insertar/actualizar libro"""
        if not self.access_token:
            if not self._ensure_valid_token():
                return
        
        # Generar ISBN único para evitar conflictos
        isbn = f"978-0-{random.randint(100000, 999999)}-{random.randint(10, 99)}-{random.randint(0, 9)}"
        
        # Crear XML del libro
        book_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<book isbn="{isbn}">
  <title>Libro de Prueba {random.randint(1, 1000)}</title>
  <author>{random.choice(TEST_AUTHORS)}</author>
  <publication_year>{random.randint(1900, 2024)}</publication_year>
  <genre>{random.choice(TEST_GENRES)}</genre>
  <price>{round(random.uniform(10.0, 100.0), 2)}</price>
  <stock>{random.choice(["true", "false"])}</stock>
  <format>{random.choice(TEST_FORMATS)}</format>
</book>'''
        
        with self.client.put(
            "/api/books/insert",
            data=book_xml,
            headers={
                **self.get_auth_headers(),
                "Content-Type": "application/xml"
            },
            catch_response=True,
            name="Insert Book"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 401:
                self.access_token = None
                if self._try_refresh_token():
                    response.success()
                    return
                response.failure("Token expired")
            else:
                response.failure(f"Insert failed: {response.status_code}")
    
    @task(3)
    def update_book(self):
        """PUT /api/books/update - Actualizar libro"""
        if not self.access_token:
            if not self._ensure_valid_token():
                return
        
        # Usar un ISBN existente o generar uno nuevo
        isbn = random.choice(TEST_ISBNS)
        
        book_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<book isbn="{isbn}">
  <title>Libro Actualizado {random.randint(1, 1000)}</title>
  <author>{random.choice(TEST_AUTHORS)}</author>
  <publication_year>{random.randint(1900, 2024)}</publication_year>
  <genre>{random.choice(TEST_GENRES)}</genre>
  <price>{round(random.uniform(10.0, 100.0), 2)}</price>
  <stock>{random.choice(["true", "false"])}</stock>
  <format>{random.choice(TEST_FORMATS)}</format>
</book>'''
        
        with self.client.put(
            "/api/books/update",
            data=book_xml,
            headers={
                **self.get_auth_headers(),
                "Content-Type": "application/xml"
            },
            catch_response=True,
            name="Update Book"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 401:
                self.access_token = None
                if self._try_refresh_token():
                    response.success()
                    return
                response.failure("Token expired")
            else:
                response.failure(f"Update failed: {response.status_code}")
    
    @task(2)
    def delete_book(self):
        """DELETE /api/books/delete - Eliminar libro"""
        if not self.access_token:
            if not self._ensure_valid_token():
                return
        
        # Usar un ISBN de prueba (solo si existe)
        isbn = random.choice(TEST_ISBNS)
        
        delete_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<books>
  <isbn>{isbn}</isbn>
</books>'''
        
        with self.client.delete(
            "/api/books/delete",
            data=delete_xml,
            headers={
                **self.get_auth_headers(),
                "Content-Type": "application/xml"
            },
            catch_response=True,
            name="Delete Book"
        ) as response:
            # Aceptar 200 incluso si el libro no existe
            if response.status_code in [200, 404]:
                response.success()
            elif response.status_code == 401:
                self.access_token = None
                if self._try_refresh_token():
                    response.success()
                    return
                response.failure("Token expired")
            else:
                response.failure(f"Delete failed: {response.status_code}")
    
    # ========== ENDPOINTS DE CATÁLOGOS ==========
    
    @task(5)
    def get_formats(self):
        """GET /api/formats - Obtener formatos disponibles"""
        if not self.access_token:
            if not self._ensure_valid_token():
                return
        
        with self.client.get(
            "/api/formats",
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Get Formats"
        ) as response:
            if response.status_code == 401:
                self.access_token = None
                if self._try_refresh_token():
                    response.success()
                    return
                response.failure("Token expired")
            elif response.status_code != 200:
                response.failure(f"Request failed: {response.status_code}")
            else:
                response.success()
    
    @task(5)
    def get_genres(self):
        """GET /api/genres - Obtener géneros disponibles"""
        if not self.access_token:
            if not self._ensure_valid_token():
                return
        
        with self.client.get(
            "/api/genres",
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Get Genres"
        ) as response:
            if response.status_code == 401:
                self.access_token = None
                if self._try_refresh_token():
                    response.success()
                    return
                response.failure("Token expired")
            elif response.status_code != 200:
                response.failure(f"Request failed: {response.status_code}")
            else:
                response.success()
    
    # ========== ENDPOINTS ADMIN ==========
    
    @task(1)
    def revoke_all_tokens(self):
        """POST /api/auth/revoke-all - Revocar todos los tokens del usuario"""
        if not self.access_token:
            return
        
        with self.client.post(
            "/api/auth/revoke-all",
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Revoke All Tokens"
        ) as response:
            if response.status_code == 200:
                response.success()
                # Limpiar tokens después de revocar
                self.access_token = None
                self.refresh_token = None
            elif response.status_code == 401:
                self.access_token = None
                if self._try_refresh_token():
                    response.success()
                    return
                response.failure("Token expired")
            else:
                response.failure(f"Revoke failed: {response.status_code}")


# Eventos para estadísticas personalizadas
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print(f"\n🚀 Iniciando pruebas de carga en: {HOST}")
    print(f"📊 Usuarios simultáneos: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print(f"📈 Tasa de spawn: {environment.runner.spawn_rate if hasattr(environment.runner, 'spawn_rate') else 'N/A'}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n✅ Pruebas de carga completadas\n")

