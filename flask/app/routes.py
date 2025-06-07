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
    """Chat endpoint handling streaming responses from Ollama."""
    try:
        # Authenticate user
        user = auth()
        
        # Initialize chat for this user
        chat = Chat(user)

        if flask.request.method == 'DELETE':
            # Delete history and get new welcome message
            new_history = chat.delete_history()
            return flask.jsonify({
                "status": "success",
                "history": new_history
            }), 200
            
        # Handle POST request
        request_data = flask.request.get_json()
        
        # If it's just requesting initial history
        if request_data.get("initial_load"):
            return flask.jsonify({"history": chat.get_history()}), 200
            
        try:
            # Process the message and get streaming response
            response = chat.process_message(request_data["prompt"])
            
            def generate():
                collected_response = ""
                try:
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                if chunk.get("message", {}).get("content"):
                                    content = chunk["message"]["content"]
                                    collected_response += content
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                            except json.JSONDecodeError:
                                log.warning(f"Failed to parse chunk: {line}")
                                continue
                    
                    # After streaming is done, save the complete response to history
                    if collected_response:
                        chat._add_message(collected_response.strip(), "assistant")
                        chat._save()
                        
                except Exception as e:
                    log.error(f"Error in stream processing: {str(e)}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                finally:
                    yield "data: [DONE]\n\n"
            
            return flask.Response(generate(), mimetype='text/event-stream')
                
        except (json.JSONDecodeError, ValueError) as e:
            log.error(f"Error in Ollama request: {str(e)}")
            return flask.jsonify({"error": str(e)}), 500
            
    except Exception as e:
        log.error(f"Error in chat endpoint: {str(e)}")
        return flask.jsonify({"error": str(e)}), 500
