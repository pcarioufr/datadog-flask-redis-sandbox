import flask
from flask import current_app as app
from app.logs import log
from app.services.chat_service import ChatService
from .auth import auth
from flask import jsonify, request
from ddtrace import tracer
from app.logs import log
import requests


@app.route("/ui/config", methods=['GET', 'POST'])
def config():
    """Endpoint for managing chat configuration (model and prompt)."""
    try:
        # Authenticate user
        user = auth()
        
        # Initialize chat service
        chat_service = ChatService(app.redis_client, user)

        if flask.request.method == 'GET':
            try:
                # Try to get current configuration
                config = chat_service.get_config()
                return flask.jsonify({
                    "status": "success",
                    "model": config['model'],
                    "prompt": config['prompt']
                }), 200
            except ValueError as e:
                # If configuration is missing, return empty config
                return flask.jsonify({
                    "status": "success",
                    "model": None,
                    "prompt": None
                }), 200
            
        # Handle POST request
        request_data = flask.request.get_json()
        
        # Update configuration
        config = chat_service.set_config(
            model=request_data.get('model'),
            prompt=request_data.get('prompt')
        )
        
        return flask.jsonify({
            "status": "success",
            "model": config['model'],
            "prompt": config['prompt']
        }), 200
            
    except Exception as e:
        log.error(f"Error in config endpoint: {str(e)}")
        return flask.jsonify({"error": str(e)}), 500

@app.route("/ui/models", methods=['GET'])
def models():
    """Endpoint for getting available models."""
    try:
        ollama_url = "http://host.docker.internal:11434/api/tags"
        response = requests.get(ollama_url, timeout=3)
        response.raise_for_status()
        data = response.json()
        models = [m['name'] for m in data.get('models', []) if 'name' in m]
        return flask.jsonify({"status": "success", "models": models}), 200
    except requests.exceptions.RequestException as e:
        log.error(f"Request error getting models: {str(e)}")
        return flask.jsonify({
            "error": f"Failed to get models: {str(e)}"
        }), 500
    except Exception as e:
        log.error(f"Unexpected error getting models: {str(e)}")
        return flask.jsonify({
            "error": "Failed to get models"
        }), 500
    
    
@app.route("/ui/prompt/default", methods=['GET'])
def default_prompt():
    """Endpoint for getting the default prompt."""
    try:
        with open('/flask/default_prompt.txt', 'r') as f:
            default_prompt = f.read().strip()
        return flask.jsonify({
            "status": "success",
            "prompt": default_prompt
        }), 200
    except Exception as e:
        log.error(f"Error getting default prompt: {str(e)}")
        return flask.jsonify({
            "error": "Failed to load default prompt",
            "prompt": "You are a helpful AI assistant."
        }), 500 