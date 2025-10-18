// JWT + Redis Books API Frontend Application
class JWTBooksApp {
    constructor() {
        this.baseURL = 'http://136.115.136.5:5003';
        this.accessToken = localStorage.getItem('accessToken') || null;
        this.refreshToken = localStorage.getItem('refreshToken') || null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateTokenDisplay();
        this.updateStatus();
        this.loadConfig();
        
        // Only load formats and genres if user is authenticated
        if (this.accessToken) {
            this.loadFormats();
            this.loadGenres();
        }
    }

    setupEventListeners() {
        // Form submissions
        const loginForm = document.getElementById('loginForm');
        if (loginForm) loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        
        const registerForm = document.getElementById('registerForm');
        if (registerForm) registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        
        const createBookForm = document.getElementById('createBookForm');
        if (createBookForm) createBookForm.addEventListener('submit', (e) => this.handleCreateBook(e));

        // Button clicks
        const refreshTokenBtn = document.getElementById('refreshTokenBtn');
        if (refreshTokenBtn) refreshTokenBtn.addEventListener('click', () => this.refreshAccessToken());

        // Books buttons
        const getAllBooksBtn = document.getElementById('getAllBooksBtn');
        if (getAllBooksBtn) getAllBooksBtn.addEventListener('click', () => this.getAllBooks());
        
        const getFormatsBtn = document.getElementById('getFormatsBtn');
        if (getFormatsBtn) getFormatsBtn.addEventListener('click', () => this.getFormats());
        
        const getGenresBtn = document.getElementById('getGenresBtn');
        if (getGenresBtn) getGenresBtn.addEventListener('click', () => this.getGenres());
        
        const searchIsbnBtn = document.getElementById('searchIsbnBtn');
        if (searchIsbnBtn) searchIsbnBtn.addEventListener('click', () => this.searchByIsbn());
        
        const searchFormatBtn = document.getElementById('searchFormatBtn');
        if (searchFormatBtn) searchFormatBtn.addEventListener('click', () => this.searchByFormat());
        
        const searchAuthorBtn = document.getElementById('searchAuthorBtn');
        if (searchAuthorBtn) searchAuthorBtn.addEventListener('click', () => this.searchByAuthor());
        
        const updateBookBtn = document.getElementById('updateBookBtn');
        if (updateBookBtn) updateBookBtn.addEventListener('click', () => this.updateBook());
        
        const deleteBookBtn = document.getElementById('deleteBookBtn');
        if (deleteBookBtn) deleteBookBtn.addEventListener('click', () => this.deleteBook());

        // Header buttons
        const configBtn = document.getElementById('configBtn');
        if (configBtn) {
            configBtn.addEventListener('click', () => {
                console.log('🔧 Botón de configuración clickeado');
                this.openConfigModal();
            });
        }
        
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) logoutBtn.addEventListener('click', () => this.logout());

        // Configuration modal
        const configForm = document.getElementById('configForm');
        if (configForm) configForm.addEventListener('submit', (e) => this.handleConfigSubmit(e));
        
        const testConnectionBtn = document.getElementById('testConnectionBtn');
        if (testConnectionBtn) testConnectionBtn.addEventListener('click', () => this.testConnection());
        
        const closeBtn = document.querySelector('.close');
        if (closeBtn) closeBtn.addEventListener('click', () => this.closeConfigModal());
        
        const configModal = document.getElementById('configModal');
        if (configModal) {
            configModal.addEventListener('click', (e) => {
            if (e.target.id === 'configModal') this.closeConfigModal();
        });
        }
    }

    // API Helper Methods
    async makeRequest(endpoint, options = {}) {
        console.log('🚀 makeRequest iniciado:', endpoint);
        const url = `${this.baseURL}${endpoint}`;
        console.log('🌐 URL completa:', url);
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        // Add Authorization header if we have an access token
        if (this.accessToken && !options.skipAuth) {
            defaultOptions.headers['Authorization'] = `Bearer ${this.accessToken}`;
            console.log('🔑 Token de autorización agregado:', this.accessToken.substring(0, 20) + '...');
        } else {
            console.log('⚠️ Sin token de autorización - accessToken:', this.accessToken ? 'Presente' : 'Ausente', 'skipAuth:', options.skipAuth);
        }

        // Merge headers properly to preserve Authorization
        const finalHeaders = { ...defaultOptions.headers, ...(options.headers || {}) };
        const finalOptions = { 
            ...defaultOptions, 
            ...options,
            headers: finalHeaders
        };
        console.log('📤 Headers finales:', finalHeaders);
        console.log('📤 Opciones finales:', finalOptions);
        
        try {
            console.log('📡 Enviando petición...');
            const response = await fetch(url, finalOptions);
            console.log('📨 Respuesta recibida:', response.status, response.statusText);
            
            // Handle XML responses
            if (response.headers.get('content-type')?.includes('application/xml')) {
                const xmlText = await response.text();
                console.log('📊 Datos XML:', xmlText);
                return { success: response.ok, status: response.status, data: xmlText };
            } else {
                const data = await response.json();
                console.log('📊 Datos de respuesta:', data);
            return { success: response.ok, status: response.status, data };
            }
        } catch (error) {
            console.error('❌ Error en petición:', error);
            return { success: false, error: error.message };
        }
    }

    // Authentication Methods
    async handleLogin(e) {
        e.preventDefault();
        console.log('🔐 Iniciando login...');
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        console.log('👤 Usuario:', username);

        const result = await this.makeRequest('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        console.log('📊 Resultado del login:', result);

        if (result.success) {
            this.accessToken = result.data.access_token;
            this.refreshToken = result.data.refresh_token;
            this.saveTokens();
            this.updateTokenDisplay();
            this.updateStatus();
            this.showGridMessage('loginMessages', 'Login exitoso!', 'success');
            document.getElementById('loginForm').reset();
            
            // Load formats and genres after successful login
            this.loadFormats();
            this.loadGenres();
        } else {
            this.showGridMessage('loginMessages', 'Error en login: ' + (result.data?.msg || 'Error desconocido'), 'error');
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        const username = document.getElementById('regUsername').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;

        const result = await this.makeRequest('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });

        if (result.success) {
            this.showGridMessage('registerMessages', 'Usuario registrado exitosamente!', 'success');
            document.getElementById('registerForm').reset();
        } else {
            this.showGridMessage('registerMessages', 'Error en registro: ' + (result.data?.msg || 'Error desconocido'), 'error');
        }
    }

    async refreshAccessToken() {
        if (!this.refreshToken) {
            this.showGridMessage('refreshMessages', 'No hay refresh token disponible', 'error');
            return;
        }

        try {
            const result = await this.makeRequest('/api/auth/refresh', {
                method: 'POST',
                body: JSON.stringify({ refresh_token: this.refreshToken }),
                skipAuth: true
            });

            if (result.success) {
                this.accessToken = result.data.access_token;
                this.saveTokens();
                this.updateTokenDisplay();
                this.showGridMessage('refreshMessages', 'Token refrescado exitosamente!', 'success');
            } else {
                this.showGridMessage('refreshMessages', 'Error al refrescar token: ' + (result.data?.msg || 'Error desconocido'), 'error');
            }
        } catch (error) {
            console.error('Error en refresh token:', error);
            this.showGridMessage('refreshMessages', 'Error de conexión: ' + error.message, 'error');
        }
    }

    logout() {
        if (this.accessToken || this.refreshToken) {
            // Try to revoke tokens on server
            this.makeRequest('/api/auth/logout', {
                method: 'POST',
                body: JSON.stringify({ 
                    access_token: this.accessToken,
                    refresh_token: this.refreshToken 
                })
            }).catch(() => {
                // Ignore errors on logout
            });
        }
        
        this.accessToken = null;
        this.refreshToken = null;
        this.clearTokens();
        this.updateTokenDisplay();
        this.updateStatus();
        this.showSuccess('Sesión cerrada exitosamente!');
    }

    // Profile Methods
    async getProfile() {
        console.log('🔍 Iniciando getProfile...');
        const result = await this.makeRequest('/api/profile');
        console.log('📊 Resultado del perfil:', result);
        
        if (result.success) {
            const profile = result.data;
            const profileHTML = `
                <div class="profile-item-card">
                    <h4>👤 Usuario</h4>
                    <p>${profile.username}</p>
                </div>
                <div class="profile-item-card">
                    <h4>📧 Email</h4>
                    <p>${profile.email}</p>
                </div>
                <div class="profile-item-card">
                    <h4>🆔 ID</h4>
                    <p>${profile.id}</p>
                </div>
                <div class="profile-item-card">
                    <h4>📅 Creado en</h4>
                    <p>${new Date(profile.created_at).toLocaleDateString('es-ES', { 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    })}</p>
                </div>
            `;
            document.getElementById('profileData').innerHTML = profileHTML;
            this.showGridMessage('profileMessages', 'Perfil obtenido exitosamente!', 'success');
        } else {
            this.showGridMessage('profileMessages', 'Error al obtener perfil: ' + (result.data?.msg || 'Error desconocido'), 'error');
        }
    }

    // Books Methods
    async getAllBooks() {
        console.log('📚 Obteniendo todos los libros...');
        console.log('🔑 Token actual:', this.accessToken ? 'Presente' : 'Ausente');
        
        const result = await this.makeRequest('/api/books');
        console.log('📊 Resultado de getAllBooks:', result);
        
        if (result.success) {
            this.displayBooksXML(result.data);
            this.showGridMessage('booksMessages', 'Libros obtenidos exitosamente!', 'success');
        } else {
            this.showGridMessage('booksMessages', 'Error al obtener libros: ' + (result.data?.msg || 'Error desconocido'), 'error');
        }
    }

    async searchByIsbn() {
        const isbn = document.getElementById('searchIsbn').value;
        if (!isbn) {
            this.showGridMessage('booksMessages', 'Por favor ingresa un ISBN', 'error');
            return;
        }

        const result = await this.makeRequest(`/api/books/${encodeURIComponent(isbn)}`);
        
        if (result.success) {
            this.displayBooksXML(result.data);
            this.showGridMessage('booksMessages', `Libro con ISBN ${isbn} encontrado!`, 'success');
        } else {
            this.showGridMessage('booksMessages', 'Error al buscar libro: ' + (result.data?.msg || 'Error desconocido'), 'error');
        }
    }

    async searchByFormat() {
        const format = document.getElementById('searchFormat').value;
        if (!format) {
            this.showGridMessage('booksMessages', 'Por favor selecciona un formato', 'error');
            return;
        }

        const result = await this.makeRequest(`/api/books/format/${encodeURIComponent(format)}`);
        
        if (result.success) {
            this.displayBooksXML(result.data);
            this.showGridMessage('booksMessages', `Libros con formato ${format} encontrados!`, 'success');
        } else {
            this.showGridMessage('booksMessages', 'Error al buscar libros: ' + (result.data?.msg || 'Error desconocido'), 'error');
        }
    }

    async searchByAuthor() {
        const author = document.getElementById('searchAuthor').value;
        if (!author) {
            this.showGridMessage('booksMessages', 'Por favor ingresa un autor', 'error');
            return;
        }

        const result = await this.makeRequest(`/api/books/author/${encodeURIComponent(author)}`);
        
        if (result.success) {
            this.displayBooksXML(result.data);
            this.showGridMessage('booksMessages', `Libros de ${author} encontrados!`, 'success');
        } else {
            this.showGridMessage('booksMessages', 'Error al buscar libros: ' + (result.data?.msg || 'Error desconocido'), 'error');
        }
    }

    async getFormats() {
        const result = await this.makeRequest('/api/formats');
        
        if (result.success) {
            this.displayFormatsXML(result.data);
            this.showGridMessage('booksMessages', 'Formatos obtenidos exitosamente!', 'success');
        } else {
            this.showGridMessage('booksMessages', 'Error al obtener formatos: ' + (result.data?.msg || 'Error desconocido'), 'error');
        }
    }

    async getGenres() {
        const result = await this.makeRequest('/api/genres');
        
        if (result.success) {
            this.displayGenresXML(result.data);
            this.showGridMessage('booksMessages', 'Géneros obtenidos exitosamente!', 'success');
        } else {
            this.showGridMessage('booksMessages', 'Error al obtener géneros: ' + (result.data?.msg || 'Error desconocido'), 'error');
        }
    }

    async handleCreateBook(e) {
        e.preventDefault();
        console.log('📚 Creando libro...');
        console.log('🔑 Token antes de crear libro:', this.accessToken ? 'Presente' : 'Ausente');
        
        const bookData = this.getBookFormData();
        
        const xmlData = this.createBookXML(bookData);
        
        const result = await this.makeRequest('/api/books/insert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/xml',
            },
            body: xmlData
        });

        if (result.success) {
            this.showGridMessage('booksMessages', 'Libro creado exitosamente!', 'success');
            document.getElementById('createBookForm').reset();
        } else {
            this.showGridMessage('booksMessages', 'Error al crear libro: ' + (result.data?.msg || 'Error desconocido'), 'error');
        }
    }

    async updateBook() {
        const bookData = this.getBookFormData();
        
        const xmlData = this.createBookXML(bookData);
        
        const result = await this.makeRequest('/api/books/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/xml',
            },
            body: xmlData
        });

        if (result.success) {
            this.showGridMessage('booksMessages', 'Libro actualizado exitosamente!', 'success');
        } else {
            this.showGridMessage('booksMessages', 'Error al actualizar libro: ' + (result.data?.msg || 'Error desconocido'), 'error');
        }
    }

    async deleteBook() {
        const isbn = document.getElementById('deleteIsbn').value;
        if (!isbn) {
            this.showGridMessage('booksMessages', 'Por favor ingresa un ISBN', 'error');
            return;
        }

        const xmlData = `<isbn>${isbn}</isbn>`;
        
        const result = await this.makeRequest('/api/books/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/xml',
            },
            body: xmlData
        });
        
        if (result.success) {
            this.showGridMessage('booksMessages', 'Libro eliminado exitosamente!', 'success');
            document.getElementById('deleteIsbn').value = '';
        } else {
            this.showGridMessage('booksMessages', 'Error al eliminar libro: ' + (result.data?.msg || 'Error desconocido'), 'error');
        }
    }

    // Helper Methods
    getBookFormData() {
        return {
            isbn: document.getElementById('bookIsbn').value,
            title: document.getElementById('bookTitle').value,
            author: document.getElementById('bookAuthor').value,
            year: document.getElementById('bookYear').value,
            genre: document.getElementById('bookGenre').value,
            price: document.getElementById('bookPrice').value,
            stock: document.getElementById('bookStock').value,
            format: document.getElementById('bookFormat').value
        };
    }

    createBookXML(bookData) {
        return `<?xml version="1.0" encoding="UTF-8"?>
<book isbn="${bookData.isbn}">
    <title>${bookData.title}</title>
    <author>${bookData.author}</author>
    <publication_year>${bookData.year}</publication_year>
    <genre>${bookData.genre}</genre>
    <price>${bookData.price}</price>
    <stock>${bookData.stock}</stock>
    <format>${bookData.format}</format>
</book>`;
    }

    displayBooksXML(xmlData) {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlData, 'text/xml');
        const books = xmlDoc.querySelectorAll('book');
        
        let html = '<div class="books-container">';
        
        if (books.length === 0) {
            html += '<p>No se encontraron libros</p>';
            } else {
            books.forEach(book => {
                const isbn = book.getAttribute('isbn');
                const title = book.querySelector('title')?.textContent || 'Sin título';
                const author = book.querySelector('author')?.textContent || 'Sin autor';
                const year = book.querySelector('publication_year')?.textContent || 'Sin año';
                const genre = book.querySelector('genre')?.textContent || 'Sin género';
                const price = book.querySelector('price')?.textContent || '0';
                const stock = book.querySelector('stock')?.textContent === 'true' ? 'Disponible' : 'Agotado';
                const format = book.querySelector('format')?.textContent || 'Sin formato';
                
                html += `
                    <div class="book-card">
                        <h4>${title}</h4>
                        <p><strong>ISBN:</strong> ${isbn}</p>
                        <p><strong>Autor:</strong> ${author}</p>
                        <p><strong>Año:</strong> ${year}</p>
                        <p><strong>Género:</strong> ${genre}</p>
                        <p><strong>Precio:</strong> $${price}</p>
                        <p><strong>Stock:</strong> ${stock}</p>
                        <p><strong>Formato:</strong> ${format}</p>
                    </div>
                `;
            });
        }
        
        html += '</div>';
        document.getElementById('resultsContainer').innerHTML = html;
    }

    displayFormatsXML(xmlData) {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlData, 'text/xml');
        const formats = xmlDoc.querySelectorAll('format');
        
        let html = '<div class="formats-container">';
        
        if (formats.length === 0) {
            html += '<p>No se encontraron formatos</p>';
        } else {
            html += '<h4>Formatos disponibles:</h4><ul>';
            formats.forEach(format => {
                const id = format.querySelector('id')?.textContent;
                const name = format.querySelector('name')?.textContent;
                html += `<li>${name} (ID: ${id})</li>`;
            });
            html += '</ul>';
        }
        
        html += '</div>';
        document.getElementById('resultsContainer').innerHTML = html;
    }

    displayGenresXML(xmlData) {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlData, 'text/xml');
        const genres = xmlDoc.querySelectorAll('genre');
        
        let html = '<div class="genres-container">';
        
        if (genres.length === 0) {
            html += '<p>No se encontraron géneros</p>';
        } else {
            html += '<h4>Géneros disponibles:</h4><ul>';
            genres.forEach(genre => {
                const id = genre.querySelector('id')?.textContent;
                const name = genre.querySelector('name')?.textContent;
                html += `<li>${name} (ID: ${id})</li>`;
            });
            html += '</ul>';
        }
        
        html += '</div>';
        document.getElementById('resultsContainer').innerHTML = html;
    }

    async loadFormats() {
        console.log('📋 Cargando formatos...');
        const result = await this.makeRequest('/api/formats');
        
        if (result.success) {
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(result.data, 'text/xml');
            const formats = xmlDoc.querySelectorAll('format');
            
            const formatSelects = ['searchFormat', 'bookFormat'];
            formatSelects.forEach(selectId => {
                const select = document.getElementById(selectId);
                if (select) {
                    // Clear existing options except first
                    while (select.children.length > 1) {
                        select.removeChild(select.lastChild);
                    }
                    
                    formats.forEach(format => {
                        const name = format.querySelector('name')?.textContent;
                        if (name) {
                            const option = document.createElement('option');
                            option.value = name;
                            option.textContent = name;
                            select.appendChild(option);
                        }
                    });
                    console.log(`✅ Formatos cargados en ${selectId}:`, select.children.length - 1, 'opciones');
                }
            });
        }
    }

    async loadGenres() {
        console.log('📚 Cargando géneros...');
        const result = await this.makeRequest('/api/genres');
        
        if (result.success) {
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(result.data, 'text/xml');
            const genres = xmlDoc.querySelectorAll('genre');
            
            const genreSelect = document.getElementById('bookGenre');
            if (genreSelect) {
                // Clear existing options except first
                while (genreSelect.children.length > 1) {
                    genreSelect.removeChild(genreSelect.lastChild);
                }
                
                genres.forEach(genre => {
                    const name = genre.querySelector('name')?.textContent;
                    if (name) {
                        const option = document.createElement('option');
                        option.value = name;
                        option.textContent = name;
                        genreSelect.appendChild(option);
                    }
                });
                console.log('✅ Géneros cargados:', genreSelect.children.length - 1, 'opciones');
            }
        }
    }

    // Configuration Methods
    openConfigModal() {
        console.log('🔧 Abriendo modal de configuración...');
        const modal = document.getElementById('configModal');
        if (modal) {
            modal.style.display = 'flex';
            modal.classList.add('show');
            console.log('✅ Modal abierto correctamente');
        } else {
            console.error('❌ Modal no encontrado');
        }
    }

    closeConfigModal() {
        const modal = document.getElementById('configModal');
        modal.style.display = 'none';
        modal.classList.remove('show');
    }

    async handleConfigSubmit(e) {
        e.preventDefault();
        const ip = document.getElementById('serviceIP').value;
        const port = document.getElementById('servicePort').value;
        const protocol = document.getElementById('serviceProtocol').value;
        
        this.baseURL = `${protocol}://${ip}:${port}`;
        this.saveConfig();
        this.updateStatus();
        this.showModalMessage('Configuración guardada exitosamente!', 'success');
    }

    async testConnection() {
        const ip = document.getElementById('serviceIP').value;
        const port = document.getElementById('servicePort').value;
        const protocol = document.getElementById('serviceProtocol').value;
        const testURL = `${protocol}://${ip}:${port}`;
        
        const button = document.getElementById('testConnectionBtn');
        const originalText = button.textContent;
        button.textContent = '🔄 Probando...';
        button.disabled = true;
        
        try {
            const response = await fetch(`${testURL}/api/health`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                mode: 'cors'
            });

            if (response.ok) {
                const data = await response.json();
                this.showModalMessage(`Conexión exitosa! Estado: ${data.status}`, 'success');
            } else {
                this.showModalMessage(`Servicio respondió con error: ${response.status}`, 'error');
            }
        } catch (error) {
            this.showModalMessage(`Error de conexión: ${error.message}`, 'error');
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    }

    // Token Management
    saveTokens() {
        if (this.accessToken) {
            localStorage.setItem('accessToken', this.accessToken);
            console.log('💾 Access token guardado en localStorage');
        }
        if (this.refreshToken) {
            localStorage.setItem('refreshToken', this.refreshToken);
            console.log('💾 Refresh token guardado en localStorage');
        }
    }

    clearTokens() {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
    }

    updateTokenDisplay() {
        const accessTokenDisplay = document.getElementById('accessTokenDisplay');
        const refreshTokenDisplay = document.getElementById('refreshTokenDisplay');
        
        if (this.accessToken) {
            accessTokenDisplay.textContent = this.accessToken.substring(0, 50) + '...';
        } else {
            accessTokenDisplay.textContent = 'No disponible';
        }
        
        if (this.refreshToken) {
            refreshTokenDisplay.textContent = this.refreshToken.substring(0, 50) + '...';
        } else {
            refreshTokenDisplay.textContent = 'No disponible';
        }
    }

    updateStatus() {
        const statusElement = document.getElementById('status');
        if (this.accessToken) {
            statusElement.textContent = '✅ Usuario Logueado';
            statusElement.className = 'status connected';
        } else {
            statusElement.textContent = '❌ No Logueado';
            statusElement.className = 'status disconnected';
        }
    }

    // Configuration Management
    saveConfig() {
        const config = {
            ip: document.getElementById('serviceIP').value,
            port: document.getElementById('servicePort').value,
            protocol: document.getElementById('serviceProtocol').value
        };
        localStorage.setItem('jwtConfig', JSON.stringify(config));
    }

    loadConfig() {
        const savedConfig = localStorage.getItem('jwtConfig');
        if (savedConfig) {
            const config = JSON.parse(savedConfig);
            document.getElementById('serviceIP').value = config.ip || '136.115.136.5';
            document.getElementById('servicePort').value = config.port || '5003';
            document.getElementById('serviceProtocol').value = config.protocol || 'http';
            
            this.baseURL = `${config.protocol}://${config.ip}:${config.port}`;
        }
    }

    // UI Helper Methods
    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type) {
        const existingMessages = document.querySelectorAll('.success-message, .error-message');
        existingMessages.forEach(msg => msg.remove());

        const messageDiv = document.createElement('div');
        messageDiv.className = `${type}-message`;
        messageDiv.textContent = message;
        
        const container = document.querySelector('.container');
        container.insertBefore(messageDiv, container.firstChild);
        
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }

    showModalMessage(message, type) {
        const modalMessages = document.getElementById('modalMessages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `modal-message ${type}`;
        messageDiv.textContent = message;
        
        modalMessages.appendChild(messageDiv);
        
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }

    showGridMessage(containerId, message, type) {
        const container = document.getElementById(containerId);
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `grid-message ${type}`;
        messageDiv.textContent = message;
        
        container.appendChild(messageDiv);
        
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new JWTBooksApp();
});

// Direct function for testing connection (bypass JavaScript issues)
async function testConnectionDirect() {
    console.log('🔍 Iniciando prueba de conexión directa...');
    
    const ip = document.getElementById('serviceIP').value;
    const port = document.getElementById('servicePort').value;
    const protocol = document.getElementById('serviceProtocol').value;
    const testURL = `${protocol}://${ip}:${port}`;
    
    console.log('🌐 URL de prueba:', testURL);
    
    const button = document.getElementById('testConnectionBtn');
    const originalText = button.textContent;
    button.textContent = '🔄 Probando...';
    button.disabled = true;
    
    try {
        console.log('📡 Enviando petición a:', `${testURL}/api/health`);
        const response = await fetch(`${testURL}/api/health`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            mode: 'cors'
        });

        console.log('📨 Respuesta recibida:', response.status, response.statusText);

        if (response.ok) {
            const data = await response.json();
            console.log('✅ Datos recibidos:', data);
            showModalMessageDirect(`Conexión exitosa! Estado: ${data.status}`, 'success');
        } else {
            console.log('❌ Error HTTP:', response.status);
            showModalMessageDirect(`Servicio respondió con error: ${response.status}`, 'error');
        }
    } catch (error) {
        console.error('❌ Error de conexión:', error);
        showModalMessageDirect(`Error de conexión: ${error.message}`, 'error');
    } finally {
        button.textContent = originalText;
        button.disabled = false;
    }
}

function showModalMessageDirect(message, type) {
    console.log('💬 Mostrando mensaje:', message, type);
    const modalMessages = document.getElementById('modalMessages');
    
    // Clear previous messages
    modalMessages.innerHTML = '';
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `modal-message ${type}`;
    messageDiv.textContent = message;
    
    modalMessages.appendChild(messageDiv);
    
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 5000);
}