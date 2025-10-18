package com.jwtclient.controller;

import com.jwtclient.service.ApiService;
import com.jwtclient.service.ConfigService;
import javafx.application.Platform;
import javafx.concurrent.Task;
import javafx.fxml.FXML;
import javafx.fxml.Initializable;
import javafx.scene.control.*;
import javafx.scene.layout.HBox;
import javafx.scene.layout.VBox;
import javafx.scene.paint.Color;
import javafx.scene.shape.Circle;
import javafx.scene.text.Text;
import javafx.scene.text.TextFlow;

import java.net.URL;
import java.util.ResourceBundle;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class MainController implements Initializable {
    
    @FXML private TextField serverIpField;
    @FXML private TextField serverPortField;
    @FXML private Button saveConfigButton;
    @FXML private Circle statusIndicator;
    @FXML private Label statusLabel;
    
    @FXML private TextField loginUsernameField;
    @FXML private PasswordField loginPasswordField;
    @FXML private Button loginButton;
    
    @FXML private TextField registerUsernameField;
    @FXML private TextField registerEmailField;
    @FXML private PasswordField registerPasswordField;
    @FXML private Button registerButton;
    
    @FXML private Button refreshTokenButton;
    @FXML private Button logoutButton;
    
    @FXML private Button getProfileButton;
    @FXML private Button getItemsButton;
    @FXML private Button createItemButton;
    @FXML private TextField itemTitleField;
    @FXML private TextField itemDescriptionField;
    
    @FXML private TextArea responseArea;
    @FXML private TextArea jwtArea;
    @FXML private TextArea profileArea;
    
    private ApiService apiService;
    private ConfigService configService;
    private ScheduledExecutorService healthCheckScheduler;
    private String currentAccessToken;
    private String currentRefreshToken;
    
    @Override
    public void initialize(URL location, ResourceBundle resources) {
        apiService = new ApiService();
        configService = new ConfigService();
        
        // Cargar configuración guardada
        loadSavedConfig();
        
        // Configurar event handlers
        setupEventHandlers();
        
        // Iniciar health check periódico
        startHealthCheck();
        
        // Configurar área de respuesta
        responseArea.setEditable(false);
        jwtArea.setEditable(false);
        profileArea.setEditable(false);
        
        logMessage("Aplicación iniciada. Configura la IP y puerto del servidor.");
    }
    
    private void loadSavedConfig() {
        String ip = configService.getServerIp();
        String port = configService.getServerPort();
        
        if (ip != null && !ip.isEmpty()) {
            serverIpField.setText(ip);
        }
        if (port != null && !port.isEmpty()) {
            serverPortField.setText(port);
        }
        
        // Actualizar la URL del ApiService automáticamente con la configuración cargada
        if (ip != null && !ip.isEmpty() && port != null && !port.isEmpty()) {
            apiService.updateBaseUrl("http://" + ip + ":" + port);
            logMessage("Configuración cargada automáticamente: " + ip + ":" + port);
        }
    }
    
    private void setupEventHandlers() {
        saveConfigButton.setOnAction(e -> saveConfig());
        loginButton.setOnAction(e -> performLogin());
        registerButton.setOnAction(e -> performRegister());
        refreshTokenButton.setOnAction(e -> performRefreshToken());
        logoutButton.setOnAction(e -> performLogout());
        getProfileButton.setOnAction(e -> getProfile());
        getItemsButton.setOnAction(e -> getItems());
        createItemButton.setOnAction(e -> createItem());
    }
    
    // Métodos públicos para FXML
    @FXML
    public void saveConfig() {
        String ip = serverIpField.getText().trim();
        String port = serverPortField.getText().trim();
        
        if (ip.isEmpty() || port.isEmpty()) {
            showAlert("Error", "IP y puerto son requeridos");
            return;
        }
        
        configService.saveServerConfig(ip, port);
        apiService.updateBaseUrl("http://" + ip + ":" + port);
        logMessage("Configuración guardada: " + ip + ":" + port);
        showAlert("Éxito", "Configuración guardada correctamente");
    }
    
    @FXML
    public void performLogin() {
        String username = loginUsernameField.getText().trim();
        String password = loginPasswordField.getText();
        
        if (username.isEmpty() || password.isEmpty()) {
            showAlert("Error", "Usuario y contraseña son requeridos");
            return;
        }
        
        Task<String> loginTask = new Task<String>() {
            @Override
            protected String call() throws Exception {
                return apiService.login(username, password);
            }
        };
        
        loginTask.setOnSucceeded(e -> {
            String response = loginTask.getValue();
            logMessage("LOGIN RESPONSE: " + response);
            
            // Parsear respuesta para extraer tokens
            if (response.contains("access_token")) {
                // Extraer tokens de la respuesta JSON
                String accessToken = extractTokenFromResponse(response, "access_token");
                String refreshToken = extractTokenFromResponse(response, "refresh_token");
                
                if (accessToken != null) {
                    currentAccessToken = accessToken;
                    currentRefreshToken = refreshToken;
                    jwtArea.setText("Access Token: " + accessToken + "\n\nRefresh Token: " + refreshToken);
                    logMessage("Login exitoso. Tokens guardados.");
                }
            }
        });
        
        loginTask.setOnFailed(e -> {
            logMessage("ERROR LOGIN: " + loginTask.getException().getMessage());
            showAlert("Error", "Error en login: " + loginTask.getException().getMessage());
        });
        
        Executors.newSingleThreadExecutor().submit(loginTask);
    }
    
    @FXML
    public void performRegister() {
        String username = registerUsernameField.getText().trim();
        String email = registerEmailField.getText().trim();
        String password = registerPasswordField.getText();
        
        if (username.isEmpty() || email.isEmpty() || password.isEmpty()) {
            showAlert("Error", "Todos los campos son requeridos");
            return;
        }
        
        Task<String> registerTask = new Task<String>() {
            @Override
            protected String call() throws Exception {
                return apiService.register(username, email, password);
            }
        };
        
        registerTask.setOnSucceeded(e -> {
            String response = registerTask.getValue();
            logMessage("REGISTER RESPONSE: " + response);
            showAlert("Éxito", "Usuario registrado correctamente");
        });
        
        registerTask.setOnFailed(e -> {
            logMessage("ERROR REGISTER: " + registerTask.getException().getMessage());
            showAlert("Error", "Error en registro: " + registerTask.getException().getMessage());
        });
        
        Executors.newSingleThreadExecutor().submit(registerTask);
    }
    
    @FXML
    public void performRefreshToken() {
        if (currentRefreshToken == null) {
            showAlert("Error", "No hay refresh token disponible. Haz login primero.");
            return;
        }
        
        logMessage("🔄 Iniciando refresh token...");
        showAlert("Info", "Refrescando token de acceso...");
        
        Task<String> refreshTask = new Task<String>() {
            @Override
            protected String call() throws Exception {
                return apiService.refreshToken(currentRefreshToken);
            }
        };
        
        refreshTask.setOnSucceeded(e -> {
            String response = refreshTask.getValue();
            logMessage("REFRESH RESPONSE: " + response);
            
            String newAccessToken = extractTokenFromResponse(response, "access_token");
            if (newAccessToken != null) {
                currentAccessToken = newAccessToken;
                jwtArea.setText("Access Token: " + newAccessToken + "\n\nRefresh Token: " + currentRefreshToken);
                logMessage("✅ Token refrescado exitosamente.");
                showAlert("Éxito", "Token de acceso refrescado correctamente.");
            }
        });
        
        refreshTask.setOnFailed(e -> {
            logMessage("ERROR REFRESH: " + refreshTask.getException().getMessage());
            showAlert("Error", "Error al refrescar token: " + refreshTask.getException().getMessage());
        });
        
        Executors.newSingleThreadExecutor().submit(refreshTask);
    }
    
    @FXML
    public void performLogout() {
        if (currentRefreshToken == null) {
            showAlert("Error", "No hay refresh token disponible.");
            return;
        }
        
        Task<String> logoutTask = new Task<String>() {
            @Override
            protected String call() throws Exception {
                return apiService.logout(currentRefreshToken);
            }
        };
        
        logoutTask.setOnSucceeded(e -> {
            String response = logoutTask.getValue();
            logMessage("LOGOUT RESPONSE: " + response);
            
            currentAccessToken = null;
            currentRefreshToken = null;
            jwtArea.clear();
            logMessage("✅ Logout exitoso. Tokens limpiados.");
            showAlert("Éxito", "Sesión cerrada correctamente.");
        });
        
        logoutTask.setOnFailed(e -> {
            logMessage("ERROR LOGOUT: " + logoutTask.getException().getMessage());
            showAlert("Error", "Error en logout: " + logoutTask.getException().getMessage());
        });
        
        Executors.newSingleThreadExecutor().submit(logoutTask);
    }
    
    @FXML
    public void getProfile() {
        if (currentAccessToken == null) {
            showAlert("Error", "No hay access token disponible. Haz login primero.");
            return;
        }
        
        logMessage("👤 Obteniendo información del perfil...");
        
        Task<String> profileTask = new Task<String>() {
            @Override
            protected String call() throws Exception {
                return apiService.getProfile(currentAccessToken);
            }
        };
        
        profileTask.setOnSucceeded(e -> {
            String response = profileTask.getValue();
            logMessage("PROFILE RESPONSE: " + response);
            
            // Mostrar la información del perfil en el área específica de perfil
            profileArea.setText(response);
            showAlert("Éxito", "Información del perfil obtenida correctamente.");
        });
        
        profileTask.setOnFailed(e -> {
            logMessage("ERROR PROFILE: " + profileTask.getException().getMessage());
            showAlert("Error", "Error al obtener perfil: " + profileTask.getException().getMessage());
        });
        
        Executors.newSingleThreadExecutor().submit(profileTask);
    }
    
    @FXML
    public void getItems() {
        if (currentAccessToken == null) {
            showAlert("Error", "No hay access token disponible. Haz login primero.");
            return;
        }
        
        logMessage("📋 Obteniendo lista de items...");
        
        Task<String> itemsTask = new Task<String>() {
            @Override
            protected String call() throws Exception {
                return apiService.getItems(currentAccessToken);
            }
        };
        
        itemsTask.setOnSucceeded(e -> {
            String response = itemsTask.getValue();
            logMessage("ITEMS RESPONSE: " + response);
            
            // Mostrar la información de los items en el área específica
            profileArea.setText(response);
            showAlert("Éxito", "Lista de items obtenida correctamente.");
        });
        
        itemsTask.setOnFailed(e -> {
            logMessage("ERROR ITEMS: " + itemsTask.getException().getMessage());
            showAlert("Error", "Error al obtener items: " + itemsTask.getException().getMessage());
        });
        
        Executors.newSingleThreadExecutor().submit(itemsTask);
    }
    
    @FXML
    public void createItem() {
        if (currentAccessToken == null) {
            showAlert("Error", "No hay access token disponible. Haz login primero.");
            return;
        }
        
        String title = itemTitleField.getText().trim();
        String description = itemDescriptionField.getText().trim();
        
        if (title.isEmpty()) {
            showAlert("Error", "El título es requerido");
            return;
        }
        
        Task<String> createTask = new Task<String>() {
            @Override
            protected String call() throws Exception {
                return apiService.createItem(currentAccessToken, title, description);
            }
        };
        
        createTask.setOnSucceeded(e -> {
            String response = createTask.getValue();
            logMessage("CREATE ITEM RESPONSE: " + response);
            logMessage("✅ Item creado exitosamente.");
            showAlert("Éxito", "Item creado correctamente.");
            itemTitleField.clear();
            itemDescriptionField.clear();
        });
        
        createTask.setOnFailed(e -> {
            logMessage("ERROR CREATE ITEM: " + createTask.getException().getMessage());
            showAlert("Error", "Error al crear item: " + createTask.getException().getMessage());
        });
        
        Executors.newSingleThreadExecutor().submit(createTask);
    }
    
    
    private void startHealthCheck() {
        healthCheckScheduler = Executors.newScheduledThreadPool(1);
        healthCheckScheduler.scheduleAtFixedRate(() -> {
            Platform.runLater(() -> {
                Task<String> healthTask = new Task<String>() {
                    @Override
                    protected String call() throws Exception {
                        return apiService.healthCheck();
                    }
                };
                
                healthTask.setOnSucceeded(e -> {
                    String response = healthTask.getValue();
                    logMessage("HEALTH CHECK: " + response);
                    updateStatusIndicator("OK", Color.GREEN);
                });
                
                healthTask.setOnFailed(e -> {
                    logMessage("HEALTH CHECK FAILED: " + healthTask.getException().getMessage());
                    updateStatusIndicator("ERROR", Color.RED);
                });
                
                Executors.newSingleThreadExecutor().submit(healthTask);
            });
        }, 0, 10, TimeUnit.SECONDS);
    }
    
    private void updateStatusIndicator(String status, Color color) {
        statusIndicator.setFill(color);
        statusLabel.setText("Estado: " + status);
    }
    
    private String extractTokenFromResponse(String response, String tokenType) {
        try {
            // Buscar el token en la respuesta JSON
            String pattern = "\"" + tokenType + "\"\\s*:\\s*\"([^\"]+)\"";
            java.util.regex.Pattern p = java.util.regex.Pattern.compile(pattern);
            java.util.regex.Matcher m = p.matcher(response);
            if (m.find()) {
                return m.group(1);
            }
        } catch (Exception e) {
            logMessage("Error extrayendo token: " + e.getMessage());
        }
        return null;
    }
    
    private void logMessage(String message) {
        Platform.runLater(() -> {
            String timestamp = java.time.LocalDateTime.now().toString();
            responseArea.appendText("[" + timestamp + "] " + message + "\n");
            responseArea.setScrollTop(Double.MAX_VALUE);
        });
    }
    
    private void showAlert(String title, String message) {
        Platform.runLater(() -> {
            Alert alert = new Alert(Alert.AlertType.INFORMATION);
            alert.setTitle(title);
            alert.setHeaderText(null);
            alert.setContentText(message);
            alert.showAndWait();
        });
    }
    
    public void shutdown() {
        if (healthCheckScheduler != null) {
            healthCheckScheduler.shutdown();
        }
    }
}