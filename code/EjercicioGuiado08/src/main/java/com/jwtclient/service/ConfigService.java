package com.jwtclient.service;

import java.io.*;
import java.util.Properties;

public class ConfigService {
    private static final String CONFIG_FILE = "config.properties";
    private Properties properties;
    
    public ConfigService() {
        properties = new Properties();
        loadConfig();
    }
    
    private void loadConfig() {
        try (FileInputStream fis = new FileInputStream(CONFIG_FILE)) {
            properties.load(fis);
        } catch (FileNotFoundException e) {
            // Archivo no existe, usar valores por defecto
            properties.setProperty("server.ip", "136.115.136.5");
            properties.setProperty("server.port", "5003");
        } catch (IOException e) {
            System.err.println("Error cargando configuración: " + e.getMessage());
        }
    }
    
    public void saveServerConfig(String ip, String port) {
        properties.setProperty("server.ip", ip);
        properties.setProperty("server.port", port);
        saveConfig();
    }
    
    public String getServerIp() {
        return properties.getProperty("server.ip", "136.115.136.5");
    }
    
    public String getServerPort() {
        return properties.getProperty("server.port", "5003");
    }
    
    private void saveConfig() {
        try (FileOutputStream fos = new FileOutputStream(CONFIG_FILE)) {
            properties.store(fos, "JWT Client Configuration");
        } catch (IOException e) {
            System.err.println("Error guardando configuración: " + e.getMessage());
        }
    }
}