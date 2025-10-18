package com.jwtclient.service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class ApiService {
    private String baseUrl = "http://localhost:5003";
    
    public void updateBaseUrl(String baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    public String healthCheck() throws Exception {
        return makeRequest("GET", "/api/health", null, null);
    }
    
    public String login(String username, String password) throws Exception {
        String jsonBody = String.format(
            "{\"username\":\"%s\",\"password\":\"%s\"}", 
            username, password
        );
        return makeRequest("POST", "/api/auth/login", jsonBody, null);
    }
    
    public String register(String username, String email, String password) throws Exception {
        String jsonBody = String.format(
            "{\"username\":\"%s\",\"email\":\"%s\",\"password\":\"%s\"}", 
            username, email, password
        );
        return makeRequest("POST", "/api/auth/register", jsonBody, null);
    }
    
    public String refreshToken(String refreshToken) throws Exception {
        String jsonBody = String.format("{\"refresh_token\":\"%s\"}", refreshToken);
        return makeRequest("POST", "/api/auth/refresh", jsonBody, null);
    }
    
    public String logout(String refreshToken) throws Exception {
        String jsonBody = String.format("{\"refresh_token\":\"%s\"}", refreshToken);
        return makeRequest("POST", "/api/auth/logout", jsonBody, null);
    }
    
    public String getProfile(String accessToken) throws Exception {
        return makeRequest("GET", "/api/profile", null, accessToken);
    }
    
    public String getItems(String accessToken) throws Exception {
        return makeRequest("GET", "/api/items", null, accessToken);
    }
    
    public String createItem(String accessToken, String title, String description) throws Exception {
        String jsonBody = String.format(
            "{\"title\":\"%s\",\"description\":\"%s\"}", 
            title, description
        );
        return makeRequest("POST", "/api/items", jsonBody, accessToken);
    }
    
    private String makeRequest(String method, String endpoint, String jsonBody, String authToken) throws Exception {
        URL url = new URL(baseUrl + endpoint);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        
        connection.setRequestMethod(method);
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setRequestProperty("Accept", "application/json");
        
        if (authToken != null) {
            connection.setRequestProperty("Authorization", "Bearer " + authToken);
        }
        
        if (jsonBody != null) {
            connection.setDoOutput(true);
            try (OutputStream os = connection.getOutputStream()) {
                byte[] input = jsonBody.getBytes(StandardCharsets.UTF_8);
                os.write(input, 0, input.length);
            }
        }
        
        int responseCode = connection.getResponseCode();
        
        BufferedReader reader;
        if (responseCode >= 200 && responseCode < 300) {
            reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
        } else {
            reader = new BufferedReader(new InputStreamReader(connection.getErrorStream()));
        }
        
        StringBuilder response = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            response.append(line);
        }
        reader.close();
        
        if (responseCode >= 400) {
            throw new Exception("HTTP " + responseCode + ": " + response.toString());
        }
        
        return response.toString();
    }
}