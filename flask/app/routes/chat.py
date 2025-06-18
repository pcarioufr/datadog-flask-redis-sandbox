import json
import flask
from flask import current_app as app, request
from app.logs import log
from app.services.chat_service import StatefulChatService, StatelessChatService
from .auth import auth


def create_sse_response(response, cleanup_callback=None):
    """Create a Server-Sent Events (SSE) response from a streaming response.
    
    Args:
        response: requests.Response object from Ollama
        cleanup_callback: Optional callback function to execute after streaming completes
        
    Returns:
        Flask Response object configured for SSE
    """
    # Get the app context before creating the generator
    ctx = app.app_context()
    collected_chunks = []
    
    def stream_response():
        try:
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if chunk.get("message", {}).get("content"):
                            content = chunk["message"]["content"]
                            collected_chunks.append(content)
                            yield f"data: {json.dumps({'content': content})}\n\n"
                    except json.JSONDecodeError:
                        log.warning(f"Failed to parse chunk: {line}")
                        continue
            
            # After all chunks collected, execute cleanup callback if provided
            if cleanup_callback and collected_chunks:
                # Use the app context for the cleanup operation
                with ctx:
                    complete_response = "".join(collected_chunks).strip()
                    cleanup_callback(complete_response)
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            log.error(f"Error during streaming: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
    
    return flask.Response(stream_response(), mimetype='text/event-stream')


@app.route("/ui/chat/init", methods=['GET'])
def welcome():
    """Get a welcome message and initialize chat."""
    try:
        # Authenticate user
        user = auth()
        
        # Initialize chat service and get streaming response with cleanup callback
        chat_service = StatefulChatService(user)
        response, cleanup_callback = chat_service.get_welcome_message_stream()
        
        return create_sse_response(response, cleanup_callback)
            
    except Exception as e:
        log.error(f"Error getting welcome message: {str(e)}")
        return flask.jsonify({"error": str(e)}), 500

@app.route("/ui/chat", methods=['GET', 'POST', 'DELETE', 'HEAD'])
def ui_chat():
    """Chat endpoint handling streaming responses from Ollama."""
    try:
        # Authenticate user
        user = auth()
        
        if flask.request.method == 'HEAD':
            # For HEAD requests, just check if chat exists
            exists = StatefulChatService.exists(user.user_id)
            return '', 200 if exists else 404
            
        # Initialize chat service
        chat_service = StatefulChatService(user)
        
        if flask.request.method == 'GET':
            # Return chat status
            return flask.jsonify({
                "exists": bool(chat_service.history),
                "history": chat_service.history
            }), 200
            
        if flask.request.method == 'DELETE':
            # Delete history and return success
            chat_service.clear_history()
            return flask.jsonify({
                "status": "success"
            }), 200
            
        # Handle POST request
        request_data = flask.request.get_json()
        
        try:
            # Process the message and get streaming response with cleanup callback
            response, cleanup_callback = chat_service.process_message_stream(request_data["prompt"])
            return create_sse_response(response, cleanup_callback)
                    
        except (json.JSONDecodeError, ValueError) as e:
            log.error(f"Error in Ollama request: {str(e)}")
            return flask.jsonify({"error": str(e)}), 500
            
    except Exception as e:
        log.error(f"Error in UI chat endpoint: {str(e)}")
        return flask.jsonify({"error": str(e)}), 500

@app.route("/api/chat", methods=['POST'])
def api_chat():
    """Simple chat endpoint for programmatic API use.
    No authentication, no streaming, no persistence.
    
    Request body:
    {
        "message": "The user message to respond to",
        "prompt": "(optional) System prompt to control model behavior",
        "model": "The model to use (e.g. 'mistral:latest', 'llama2:latest', etc.)"
    }
    """
    try:
        # Get request data
        request_data = request.get_json()
        if not request_data:
            return flask.jsonify({"error": "Empty request body"}), 400
            
        if 'model' not in request_data:
            return flask.jsonify({"error": "Missing model in request"}), 400
            
        if 'message' not in request_data:
            return flask.jsonify({"error": "Missing message in request"}), 400

        # Initialize chat service with model and prompt
        chat_service = StatelessChatService(
            model=request_data['model'],
            prompt=request_data.get('prompt')
        )
        
        # Process the message
        messages = [{"role": "user", "content": request_data["message"]}]
        response = chat_service.process_message(messages)
        return flask.jsonify({"response": response})
            
    except ValueError as e:
        # Handle Ollama status errors
        return flask.jsonify({"error": str(e)}), 503
    except Exception as e:
        log.error(f"Unexpected error in API chat endpoint: {str(e)}")
        return flask.jsonify({"error": "Internal server error"}), 500 