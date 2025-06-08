import flask
from flask import current_app as app
from app.logs import log
from app.services.chat_service import ChatService
from .auth import auth

@app.route("/ui/prompt", methods=['GET', 'POST'])
def prompt():
    """Endpoint for managing chat prompts."""
    try:
        # Authenticate user
        user = auth()
        
        # Initialize chat service
        chat_service = ChatService(app.redis_client, user)

        if flask.request.method == 'GET':
            # Return current prompt
            return flask.jsonify({
                "status": "success",
                "prompt": chat_service.get_prompt()
            }), 200
            
        # Handle POST request
        request_data = flask.request.get_json()
        if not request_data or 'prompt' not in request_data:
            return flask.jsonify({
                "error": "Missing prompt in request"
            }), 400
            
        # Update prompt
        new_prompt = chat_service.set_prompt(request_data['prompt'])
        return flask.jsonify({
            "status": "success",
            "prompt": new_prompt
        }), 200
            
    except Exception as e:
        log.error(f"Error in prompt endpoint: {str(e)}")
        return flask.jsonify({"error": str(e)}), 500

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