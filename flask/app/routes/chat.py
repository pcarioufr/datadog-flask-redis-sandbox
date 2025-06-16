import json
import flask
from flask import current_app as app, request
from app.logs import log
from app.services.chat_service import StatefulChatService, StatelessChatService
from .auth import auth

from ddtrace.llmobs import LLMObs
from ddtrace.llmobs.decorators import llm


def create_stream_response(generate, collected_content, after_request=None):
    """Create a Flask SSE response from a generator.
    
    Args:
        generate: Generator function that yields message chunks
        collected_content: List to store content chunks
        after_request: Optional callback to execute after successful streaming
        
    Returns:
        Flask Response object configured for SSE
    """
    streaming_completed = False
    streaming_error = None
    
    # Capture the current Flask app instance
    flask_app = flask.current_app._get_current_object()
    
    def stream_response():
        nonlocal streaming_completed, streaming_error
        try:
            for chunk in generate():
                if 'content' in chunk:
                    yield f"data: {json.dumps({'content': chunk['content']})}\n\n"
                elif 'error' in chunk:
                    streaming_error = chunk['error']
                    yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
                elif chunk.get('done'):
                    streaming_completed = not streaming_error  # Only mark as completed if no errors
                    yield "data: [DONE]\n\n"
        except Exception as e:
            log.error(f"Error during streaming: {str(e)}")
            streaming_error = str(e)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
    
    def wrapped_after_request():
        if streaming_completed and after_request:
            # Use the captured Flask app instance
            with flask_app.app_context():
                try:
                    after_request()
                except Exception as e:
                    log.error(f"Error in after_request callback: {str(e)}")
    
    response = flask.Response(stream_response(), mimetype='text/event-stream')
    if after_request:
        response.call_on_close(wrapped_after_request)
    return response


@app.route("/ui/chat/init", methods=['GET'])
def welcome():
    """Get a welcome message and initialize chat."""
    try:
        # Authenticate user
        user = auth()
        
        # Initialize chat service and get streaming welcome message
        chat_service = StatefulChatService(user)
        generate, collected_content = chat_service.get_welcome_message()
        
        # After streaming is done, initialize chat with the collected message
        def after_request():
            if collected_content:
                chat_service.add_message("".join(collected_content).strip(), "assistant")
                
        return create_stream_response(generate, collected_content, after_request)
            
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
            # Process the message and get streaming response
            generate, collected_content = chat_service.process_message(request_data["prompt"])
            
            # After streaming starts, annotate the conversation
            def after_request():
                if collected_content:  # Check if we collected any content
                    collected_response = "".join(collected_content).strip()
                    response_data = {"role": "assistant", "content": collected_response}
                    with LLMObs.llm(model_name=chat_service.config['model'], model_provider="ollama") as span:
                        LLMObs.annotate(
                            span=span,
                            input_data=chat_service.history,  # Include all messages including user's input
                            output_data=response_data
                        )
                    # Save to chat history after successful streaming
                    chat_service.add_message(response_data["content"], "assistant")
            
            return create_stream_response(generate, collected_content, after_request)
                    
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