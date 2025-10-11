from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)  # Esto permite peticiones CORS desde cualquier origen

# API Endpoint
@app.route('/api/respuesta', methods=['POST'])
def respuesta():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos JSON"}), 400
        
        prompt = data.get('prompt', '')
        if not prompt:
            return jsonify({"error": "El campo 'prompt' es requerido"}), 400
        
        ollama_url = 'http://localhost:11434/api/generate'
        payload = {
            "model": "deepseek-coder",
            "prompt": prompt
        }
        
        # Verificar si Ollama está corriendo
        try:
            response = requests.post(ollama_url, json=payload, stream=True, timeout=30)
            response.raise_for_status()  # Esto lanzará una excepción si hay error HTTP
        except requests.exceptions.ConnectionError:
            return jsonify({"error": "No se puede conectar a Ollama. Asegúrate de que esté corriendo en http://localhost:11434"}), 503
        except requests.exceptions.Timeout:
            return jsonify({"error": "Timeout al conectar con Ollama"}), 504
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"Error al conectar con Ollama: {str(e)}"}), 500
        
        result = ""
        for line in response.iter_lines():
            if line:
                try:
                    obj = json.loads(line)
                    if 'response' in obj and obj['response']:
                        result += obj['response']
                except json.JSONDecodeError:
                    continue
        
        if not result:
            return jsonify({"error": "No se recibió respuesta de Ollama"}), 500
            
        return jsonify({"respuesta": result})
        
    except Exception as e:
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

# Página principal en la misma ruta base
@app.route('/')
def home():
    return send_file('index.html')  # Asegúrate que index.html está en el mismo folder que app.py

# Define que si llama mi app va a correr main
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)