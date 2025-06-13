import flask
from flask import current_app as app
from app.logs import log
from app.services.chat_service import ChatService
from .auth import auth
import os
import json
import requests

@app.route("/ui/model", methods=['GET', 'POST'])
def model():
    """Endpoint for getting and setting the model."""
    try:
        # Authenticate user
        user = auth()
        log.info(f"[MODEL] Authenticated user: {getattr(user, 'user_id', user)}")
        
        # Initialize chat service
        chat_service = ChatService(app.redis_client, user)
        
        if flask.request.method == 'GET':
            # Get current model
            model = chat_service.get_model()
            log.info(f"[MODEL] GET current model: {model}")
            return flask.jsonify({
                "status": "success",
                "model": model
            }), 200
            
        # Handle POST request
        request_data = flask.request.get_json()
        log.info(f"[MODEL] POST request data: {request_data}")
        if not request_data or 'model' not in request_data:
            log.error(f"[MODEL] Missing model in request: {request_data}")
            return flask.jsonify({
                "error": "Missing model in request"
            }), 400
            
        # Set new model
        model = chat_service.set_model(request_data["model"])
        log.info(f"[MODEL] Set new model: {model}")
        return flask.jsonify({
            "status": "success",
            "model": model
        }), 200
            
    except Exception as e:
        log.error(f"[MODEL] Error in model endpoint: {str(e)}", exc_info=True)
        return flask.jsonify({
            "error": str(e)
        }), 500

@app.route("/ui/models", methods=['GET'])
def list_models():
    """Fetch available models dynamically from Ollama API."""
    try:
        ollama_url = "http://host.docker.internal:11434/api/ps"
        response = requests.get(ollama_url, timeout=3)
        response.raise_for_status()
        data = response.json()
        models = [m['name'] for m in data.get('models', []) if 'name' in m]
        return flask.jsonify({"status": "success", "models": models}), 200
    except Exception as e:
        log.error(f"[MODEL] Error fetching models from Ollama: {str(e)}", exc_info=True)
        return flask.jsonify({"error": str(e), "models": []}), 500 