// JWT Authentication Frontend Application
class JWTAuthApp {
    constructor() {
        this.baseURL = 'http://34.27.138.169:5003';
        this.accessToken = localStorage.getItem('accessToken') || null;
        this.refreshToken = localStorage.getItem('refreshToken') || null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateTokenDisplay();
        this.updateStatus();
        this.loadConfig();
    }

    setupEventListeners() {
        // Form submissions
        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('registerForm').addEventListener('submit', (e) => this.handleRegister(e));
        document.getElementById('createItemForm').addEventListener('submit', (e) => this.handleCreateItem(e));

        // Button clicks
        document.getElementById('getProfileBtn').addEventListener('click', () => this.getProfile());
        document.getElementById('listItemsBtn').addEventListener('click', () => this.listItems());
        document.getElementById('refreshTokenBtn').addEventListener('click', () => this.refreshAccessToken());

        // Header buttons
        document.getElementById('configBtn').addEventListener('click', () => this.openConfigModal());
        document.getElementById('logoutBtn').addEventListener('click', () => this.logout());

        // Configuration modal
        document.getElementById('configForm').addEventListener('submit', (e) => this.handleConfigSubmit(e));
        document.getElementById('testConnectionBtn').addEventListener('click', () => this.testConnection());
        document.querySelector('.close').addEventListener('click', () => this.closeConfigModal());
        document.getElementById('configModal').addEventListener('click', (e) => {
            if (e.target.id === 'configModal') this.closeConfigModal();
        });
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
            console.log('🔑 Token de autorización agregado');
        } else {
            console.log('⚠️ Sin token de autorización');
        }

        const finalOptions = { ...defaultOptions, ...options };
        console.log('📤 Opciones finales:', finalOptions);
        
        try {
            console.log('📡 Enviando petición...');
            const response = await fetch(url, finalOptions);
            console.log('📨 Respuesta recibida:', response.status, response.statusText);
            const data = await response.json();
            console.log('📊 Datos de respuesta:', data);
            
            return { success: response.ok, status: response.status, data };
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

        // Log del refresh token que se va a usar
        console.log('Usando refresh token:', this.refreshToken.substring(0, 50) + '...');
        console.log('Refresh token completo:', this.refreshToken);

        try {
            const result = await this.makeRequest('/api/auth/refresh', {
                method: 'POST',
                body: JSON.stringify({ refresh_token: this.refreshToken }),
                skipAuth: true // No requiere access token, usa refresh token en body
            });

            console.log('Resultado del refresh:', result);

            if (result.success) {
                const oldAccessToken = this.accessToken;
                this.accessToken = result.data.access_token;
                this.saveTokens();
                this.updateTokenDisplay();
                
                console.log('Access token anterior:', oldAccessToken?.substring(0, 50) + '...');
                console.log('Access token nuevo:', this.accessToken?.substring(0, 50) + '...');
                console.log('¿Son diferentes?', oldAccessToken !== this.accessToken);
                
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

    // Items Methods
    async handleCreateItem(e) {
        e.preventDefault();
        const title = document.getElementById('itemTitle').value;
        const description = document.getElementById('itemDescription').value;

        const result = await this.makeRequest('/api/items', {
            method: 'POST',
            body: JSON.stringify({ title, description })
        });

        if (result.success) {
            this.showGridMessage('itemsMessages', 'Item creado exitosamente!', 'success');
            document.getElementById('createItemForm').reset();
            // Auto-refresh items list
            this.listItems();
        } else {
            this.showGridMessage('itemsMessages', 'Error al crear item: ' + (result.data?.msg || 'Error desconocido'), 'error');
        }
    }

    async listItems() {
        const result = await this.makeRequest('/api/items');
        
        if (result.success) {
            const itemsList = document.getElementById('itemsList');
            if (result.data.length === 0) {
                itemsList.innerHTML = '<p>No hay items disponibles</p>';
            } else {
                itemsList.innerHTML = result.data.map(item => `
                    <div class="item-card" style="background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 15px; margin: 10px 0;">
                        <h4 style="color: #495057; margin-bottom: 8px;">${item.title}</h4>
                        <p style="color: #6c757d; margin-bottom: 8px;">${item.description || 'Sin descripción'}</p>
                        <small style="color: #6c757d;">Creado: ${new Date(item.created_at).toLocaleString()}</small>
                    </div>
                `).join('');
            }
            this.showGridMessage('itemsMessages', 'Items listados exitosamente!', 'success');
        } else {
            this.showGridMessage('itemsMessages', 'Error al listar items: ' + (result.data?.msg || 'Error desconocido'), 'error');
        }
    }


    // Configuration Methods
    openConfigModal() {
        document.getElementById('configModal').classList.add('show');
    }

    closeConfigModal() {
        document.getElementById('configModal').classList.remove('show');
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
        
        // Mostrar estado de carga
        const button = document.getElementById('testConnectionBtn');
        const originalText = button.textContent;
        button.textContent = '🔄 Probando...';
        button.disabled = true;
        
        try {
            console.log('🔍 Probando conexión a:', testURL);
            
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
                console.log('✅ Conexión exitosa:', data);
                this.showModalMessage(`Conexión exitosa! Servicio disponible. Estado: ${data.status}`, 'success');
            } else {
                const errorText = await response.text();
                console.error('❌ Error HTTP:', response.status, errorText);
                this.showModalMessage(`Servicio respondió con error: ${response.status} ${response.statusText}`, 'error');
            }
        } catch (error) {
            console.error('❌ Error de conexión:', error);
            this.showModalMessage(`Error de conexión: ${error.message}`, 'error');
        } finally {
            // Restaurar botón
            button.textContent = originalText;
            button.disabled = false;
        }
    }

    // Token Management
    saveTokens() {
        if (this.accessToken) localStorage.setItem('accessToken', this.accessToken);
        if (this.refreshToken) localStorage.setItem('refreshToken', this.refreshToken);
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
            document.getElementById('serviceIP').value = config.ip || '34.27.138.169';
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
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.success-message, .error-message');
        existingMessages.forEach(msg => msg.remove());

        // Create new message
        const messageDiv = document.createElement('div');
        messageDiv.className = `${type}-message`;
        messageDiv.textContent = message;
        
        // Insert at the top of the container
        const container = document.querySelector('.container');
        container.insertBefore(messageDiv, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }

    // Modal Message Methods
    showModalMessage(message, type) {
        const modalMessages = document.getElementById('modalMessages');
        
        // Create new message
        const messageDiv = document.createElement('div');
        messageDiv.className = `modal-message ${type}`;
        messageDiv.textContent = message;
        
        // Add to modal messages
        modalMessages.appendChild(messageDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }

    // Grid Message Methods
    showGridMessage(containerId, message, type) {
        const container = document.getElementById(containerId);
        
        // Create new message
        const messageDiv = document.createElement('div');
        messageDiv.className = `grid-message ${type}`;
        messageDiv.textContent = message;
        
        // Add to grid messages
        container.appendChild(messageDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new JWTAuthApp();
});
