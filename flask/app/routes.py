import json
import flask
from flask import current_app as app
from app.logs import log
from app.models import User, Chat

def auth():
    """Handle user authentication.
    
    Currently implements a simple authentication:
    - Uses URL param if provided
    - Creates random user if no session
    - Uses existing session if available
    
    Returns:
        User: Authenticated user instance
    """

    # Login when user_id is injected as a URL param 
    if flask.request.args.get("user_id"):
        user = User(flask.request.args.get("user_id"))

    # Login as random user (when session cookie is empty)
    elif not flask.session.get("user_id"):
        user = User()

    # Recognizes an existing user (through session cookie)
    else:
        user = User.from_session()

    user.login()
    return user

@app.route("/")
def home():
    user = auth()
    return flask.render_template(
        "home.jinja",
        user_id=user.user_id,
        user_email=user.email,
        is_anonymous=False,
        clientToken=app.config["DD_CLIENT_TOKEN"],
        applicationId=app.config["DD_APPLICATION_ID"],
        dd_version=app.config["DD_VERSION"],
        dd_env=app.config["DD_ENV"],
        dd_site=app.config["DD_SITE"],
    )

@app.route("/api/ping")
def ping():
    log.info("ping successful")
    return flask.jsonify(response="pong"), 200


@app.route("/api/chat", methods=['POST', 'DELETE'])
def chat():
    """Chat endpoint handling both streaming and non-streaming responses from Ollama.
    
    TODO: Add support for streaming responses from Ollama:
    - Add a 'stream' parameter in the request to toggle streaming mode
    - When streaming is enabled:
        - Use Flask's streaming response
        - Parse Ollama's streaming response line by line
        - Send each chunk to the client
        - Handle proper message history updates
        - Consider implementing SSE (Server-Sent Events) for better client handling
    """
    try:

        # Authenticate user
        user = auth()
        
        # Initialize chat for this user
        chat = Chat(user)

        if flask.request.method == 'DELETE':
            chat.delete_history()
            return flask.jsonify({
                "status": "success",
                "history": chat.get_history()
            }), 200
            
        # Handle POST request
        request_data = flask.request.get_json()
        
        # If it's just requesting initial history
        if request_data.get("initial_load"):
            return flask.jsonify({"history": chat.get_history()}), 200
            
        try:
            # Process the message and get response
            assistant_response = chat.process_message(request_data["prompt"])
            
            return flask.jsonify({
                'response': assistant_response,
                'history': chat.get_history()
            }), 200
            
        except (json.JSONDecodeError, ValueError) as e:
            log.error(f"Error in Ollama request: {str(e)}")
            return flask.jsonify({"error": str(e)}), 500
            
    except Exception as e:
        log.error(f"Error in chat endpoint: {str(e)}")
        return flask.jsonify({"error": str(e)}), 500
