import json
import flask
from flask import current_app as app
from app.logs import log
from app.services.chat_service import ChatService
from app.services.llm_service import LLMService
from .auth import auth

@app.route("/ui/chat/init", methods=['GET'])
def welcome():
    """Get a welcome message and initialize chat."""
    try:
        # Authenticate user
        user = auth()
        
        # Initialize chat service and get streaming welcome message
        chat_service = ChatService(app.redis_client, user)
        response = chat_service.get_welcome_message()
        
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
                
                # After streaming is done, initialize chat with the collected message
                if collected_response:
                    chat_service.initialize_chat_with_message(collected_response.strip())
                    
            except Exception as e:
                log.error(f"Error in stream processing: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            finally:
                yield "data: [DONE]\n\n"
        
        return flask.Response(generate(), mimetype='text/event-stream')
            
    except Exception as e:
        log.error(f"Error getting welcome message: {str(e)}")
        return flask.jsonify({"error": str(e)}), 500

@app.route("/ui/chat", methods=['GET', 'POST', 'DELETE'])
def chat():
    """Chat endpoint handling streaming responses from Ollama."""
    try:
        # Authenticate user
        user = auth()
        
        # Initialize chat service
        chat_service = ChatService(app.redis_client, user)

        if flask.request.method == 'GET':
            # Load history (if any) and return chat status
            exists = chat_service.load_history()
            return flask.jsonify({
                "exists": exists,
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
            response = chat_service.process_message(request_data["prompt"])
            
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
                        chat_service.add_message(collected_response.strip(), "assistant")
                        
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
        log.error(f"Error in UI chat endpoint: {str(e)}")
        return flask.jsonify({"error": str(e)}), 500

@app.route("/api/chat", methods=['POST'])
def api_chat():
    """Simple chat endpoint for programmatic API use.
    No authentication, no streaming, no persistence.
    
    Request body:
    {
        "prompt": "The user message to respond to",
        "system_prompt": "(optional) System prompt to control model behavior"
    }
    """
    try:
        request_data = flask.request.get_json()
        if not request_data or 'prompt' not in request_data:
            return flask.jsonify({
                "error": "Missing prompt in request"
            }), 400

        # Prepare messages for LLM
        messages = []
        if "system_prompt" in request_data:
            messages.append({"role": "system", "content": request_data["system_prompt"]})
        messages.append({"role": "user", "content": request_data["prompt"]})

        # Get direct response from LLM service
        response = LLMService.generate_response_sync(messages)
        
        return flask.jsonify({
            "response": response
        }), 200
            
    except Exception as e:
        log.error(f"Error in API chat endpoint: {str(e)}")
        return flask.jsonify({"error": str(e)}), 500 