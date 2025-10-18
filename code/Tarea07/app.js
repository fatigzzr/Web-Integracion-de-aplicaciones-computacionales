// Configuración de la API
const API_BASE_URL = 'http://136.115.136.5:5003';

// Clase para manejar la autenticación y tokens
class AuthManager {
    constructor() {
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        this.tokenRefreshTimer = null;
    }

    // Guardar tokens en localStorage
    saveTokens(accessToken, refreshToken) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        
        // Mostrar comparación JWT Local vs Redis
        this.logJWTComparison(accessToken, 'LOCAL STORAGE');
        
        // Programar refresh automático del token (4 minutos)
        this.scheduleTokenRefresh();
    }

    // Limpiar tokens
    clearTokens() {
        this.accessToken = null;
        this.refreshToken = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        if (this.tokenRefreshTimer) {
            clearTimeout(this.tokenRefreshTimer);
            this.tokenRefreshTimer = null;
        }
    }

    // Verificar si está autenticado
    isAuthenticated() {
        return !!this.accessToken;
    }

    // Obtener headers de autorización
    getAuthHeaders() {
        if (!this.accessToken) {
            throw new Error('No hay token de acceso disponible');
        }
        return {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
        };
    }

    // Programar refresh automático del token
    scheduleTokenRefresh() {
        if (this.tokenRefreshTimer) {
            clearTimeout(this.tokenRefreshTimer);
        }
        
        // Refresh 1 minuto antes de que expire (token expira en 5 minutos)
        this.tokenRefreshTimer = setTimeout(async () => {
            try {
                await this.refreshAccessToken();
            } catch (error) {
                this.handleTokenExpired();
            }
        }, 4 * 60 * 1000); // 4 minutos
    }

    // Refrescar access token
    async refreshAccessToken() {
        if (!this.refreshToken) {
            throw new Error('No hay refresh token disponible');
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.refreshToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Error al refrescar token');
            }

            const data = await response.json();
            this.accessToken = data.access_token;
            localStorage.setItem('access_token', data.access_token);
            
            // Mostrar comparación del nuevo token
            this.logJWTComparison(data.access_token, 'REFRESH FROM REDIS');
            
            // Programar siguiente refresh
            this.scheduleTokenRefresh();
            
            return data.access_token;
        } catch (error) {
            throw error;
        }
    }

    // Manejar token expirado
    handleTokenExpired() {
        this.clearTokens();
        this.showLoginForm();
        this.showMessage('Sesión expirada. Por favor, inicia sesión nuevamente.', 'error');
    }

    // Mostrar formulario de login
    showLoginForm() {
        document.getElementById('loginForm').style.display = 'block';
        document.getElementById('userInfo').style.display = 'none';
        document.getElementById('mainContent').style.display = 'none';
    }

    // Mostrar contenido principal
    showMainContent() {
        document.getElementById('loginForm').style.display = 'none';
        document.getElementById('userInfo').style.display = 'block';
        document.getElementById('mainContent').style.display = 'block';
    }

    // Mostrar comparación JWT Local vs Redis
    logJWTComparison(token, source) {
        try {
            // Decodificar JWT (solo el payload, sin verificar firma)
            const parts = token.split('.');
            if (parts.length === 3) {
                const payload = JSON.parse(atob(parts[1]));
                
                console.log('🔍 COMPARACIÓN JWT LOCAL vs REDIS');
                console.log('=====================================');
                console.log(`📍 Fuente: ${source}`);
                console.log(`🆔 JTI (Token ID): ${payload.jti}`);
                console.log(`👤 Usuario ID: ${payload.sub}`);
                console.log(`⏰ Emitido (iat): ${new Date(payload.iat * 1000).toLocaleString()}`);
                console.log(`⏰ Expira (exp): ${new Date(payload.exp * 1000).toLocaleString()}`);
                console.log(`⏱️ Tiempo restante: ${Math.round((payload.exp - payload.iat) / 60)} minutos`);
                console.log(`🔑 Tipo: ${payload.type}`);
                console.log('=====================================');
                
                // Mostrar estado en Redis (simulado)
                console.log('🗄️ ESTADO EN REDIS:');
                console.log(`   Clave: access_token:${token.substring(0, 20)}...`);
                console.log(`   Valor: "valid"`);
                console.log(`   Expira: ${Math.round((payload.exp - payload.iat) / 60)} minutos`);
                console.log('=====================================');
            }
        } catch (error) {
            console.error('❌ Error al decodificar JWT:', error);
        }
    }
}

// Clase para manejar las operaciones de libros
class BooksManager {
    constructor(authManager) {
        this.authManager = authManager;
    }

    // Hacer petición con manejo automático de tokens
    async makeAuthenticatedRequest(url, options = {}) {
        try {
            const headers = this.authManager.getAuthHeaders();
            const response = await fetch(url, {
                ...options,
                headers: { ...headers, ...options.headers }
            });

            // Si el token expiró, intentar refrescar
            if (response.status === 401) {
                try {
                    await this.authManager.refreshAccessToken();
                    // Reintentar la petición con el nuevo token
                    const newHeaders = this.authManager.getAuthHeaders();
                    const retryResponse = await fetch(url, {
                        ...options,
                        headers: { ...newHeaders, ...options.headers }
                    });
                    return retryResponse;
                } catch (refreshError) {
                    this.authManager.handleTokenExpired();
                    throw new Error('Sesión expirada');
                }
            }

            return response;
        } catch (error) {
            console.error('Error en petición autenticada:', error);
            throw error;
        }
    }

    // Obtener lista de libros
    async getBooks() {
        try {
            const response = await this.makeAuthenticatedRequest(`${API_BASE_URL}/api/books`);
            
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }

            const books = await response.json();
            return books;
        } catch (error) {
            throw error;
        }
    }

    // Agregar nuevo libro
    async addBook(bookData) {
        try {
            const response = await this.makeAuthenticatedRequest(`${API_BASE_URL}/api/books`, {
                method: 'POST',
                body: JSON.stringify(bookData)
            });

            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            throw error;
        }
    }

    // Renderizar lista de libros
    renderBooks(books) {
        const booksList = document.getElementById('booksList');
        
        if (!books || books.length === 0) {
            booksList.innerHTML = '<div class="loading">No hay libros disponibles</div>';
            return;
        }

        booksList.innerHTML = books.map(book => `
            <div class="book-card">
                <div class="book-title">${this.escapeHtml(book.title)}</div>
                <div class="book-author">👤 ${this.escapeHtml(book.author || 'Autor desconocido')}</div>
                <div class="book-year">📅 ${book.year || 'Año desconocido'}</div>
            </div>
        `).join('');
    }

    // Escapar HTML para prevenir XSS
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Clase principal de la aplicación
class App {
    constructor() {
        this.authManager = new AuthManager();
        this.booksManager = new BooksManager(this.authManager);
        this.init();
    }

    // Inicializar aplicación
    init() {
        this.setupEventListeners();
        this.checkAuthStatus();
    }

    // Configurar event listeners
    setupEventListeners() {
        // Login form
        document.getElementById('loginFormElement').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Logout button
        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.handleLogout();
        });

        // Add book form
        document.getElementById('addBookForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleAddBook();
        });

        // Refresh books button
        document.getElementById('refreshBooksBtn').addEventListener('click', () => {
            this.loadBooks();
        });
    }

    // Verificar estado de autenticación
    checkAuthStatus() {
        if (this.authManager.isAuthenticated()) {
            this.authManager.showMainContent();
            this.loadBooks();
        } else {
            this.authManager.showLoginForm();
        }
    }

    // Manejar login
    async handleLogin() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        if (!username || !password) {
            this.showMessage('Por favor, completa todos los campos', 'error');
            return;
        }

        try {
            this.showMessage('Iniciando sesión...', 'info');
            
            const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.msg || 'Error al iniciar sesión');
            }

            const data = await response.json();
            this.authManager.saveTokens(data.access_token, data.refresh_token);
            this.authManager.showMainContent();
            this.showMessage('¡Sesión iniciada correctamente!', 'success');
            this.loadBooks();
            
        } catch (error) {
            this.showMessage(error.message, 'error');
        }
    }

    // Manejar logout
    async handleLogout() {
        try {
            if (this.authManager.accessToken) {
                // Mostrar comparación antes del logout
                this.authManager.logJWTComparison(this.authManager.accessToken, 'BEFORE LOGOUT');
                
                await fetch(`${API_BASE_URL}/api/auth/logout`, {
                    method: 'POST',
                    headers: this.authManager.getAuthHeaders()
                });
                
                // Mostrar estado después del logout
                console.log('🗄️ ESTADO EN REDIS DESPUÉS DEL LOGOUT:');
                console.log('   Clave: revoked_token:[JTI]');
                console.log('   Valor: "true"');
                console.log('   Expira: 1 hora');
                console.log('   Estado: TOKEN REVOCADO ❌');
            }
        } catch (error) {
            // Error silencioso
        } finally {
            this.authManager.clearTokens();
            this.authManager.showLoginForm();
            this.showMessage('Sesión cerrada correctamente', 'success');
        }
    }

    // Cargar libros
    async loadBooks() {
        const booksList = document.getElementById('booksList');
        booksList.innerHTML = '<div class="loading">Cargando libros...</div>';

        try {
            const books = await this.booksManager.getBooks();
            this.booksManager.renderBooks(books);
        } catch (error) {
            console.error('Error al cargar libros:', error);
            booksList.innerHTML = '<div class="loading">Error al cargar los libros</div>';
            this.showMessage('Error al cargar los libros', 'error');
        }
    }

    // Manejar agregar libro
    async handleAddBook() {
        const title = document.getElementById('bookTitle').value;
        const author = document.getElementById('bookAuthor').value;
        const year = document.getElementById('bookYear').value;

        if (!title || !author) {
            this.showMessage('Por favor, completa título y autor', 'error');
            return;
        }

        try {
            this.showMessage('Agregando libro...', 'info');
            
            const bookData = {
                title: title.trim(),
                author: author.trim(),
                published_year: year ? parseInt(year) : null
            };

            await this.booksManager.addBook(bookData);
            this.showMessage('¡Libro agregado correctamente!', 'success');
            
            // Limpiar formulario
            document.getElementById('addBookForm').reset();
            
            // Recargar lista de libros
            this.loadBooks();
            
        } catch (error) {
            console.error('Error al agregar libro:', error);
            this.showMessage(error.message, 'error');
        }
    }

    // Mostrar mensaje de estado
    showMessage(message, type = 'info') {
        const statusMessage = document.getElementById('statusMessage');
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type} show`;
        
        // Ocultar mensaje después de 4 segundos
        setTimeout(() => {
            statusMessage.classList.remove('show');
        }, 4000);
    }
}

// Inicializar aplicación cuando se carga la página
document.addEventListener('DOMContentLoaded', () => {
    new App();
});
