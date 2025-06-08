import requests
from flask import current_app as app
from ddtrace.llmobs import LLMObs
from ddtrace.llmobs.decorators import llm
import json
import logging

log = logging.getLogger(__name__)

class LLMService:
    """Service for handling LLM interactions."""
    
    @staticmethod
    @llm(model_name=app.config["OLLAMA_MODEL"], model_provider="ollama")
    def generate_response(messages, system_prompt):
        """Generate a streaming response from the LLM."""
        
        # Prepare the request for Ollama with system prompt
        ollama_request = {
            "model": app.config["OLLAMA_MODEL"],
            "messages": [
                {"role": "system", "content": system_prompt}
            ] + messages,
            "stream": True,
            "options": {
                "temperature": app.config["OLLAMA_TEMPERATURE"],
                "top_p": app.config["OLLAMA_TOP_P"],
                "num_predict": int(app.config.get("OLLAMA_NUM_PREDICT")),
                "num_ctx": int(app.config.get("OLLAMA_NUM_CTX"))
            }
        }

        # Forward the request to Ollama    
        return requests.post(
            'http://host.docker.internal:11434/api/chat',
            json=ollama_request,
            stream=True
        )
        
    @staticmethod
    def extract_content_from_stream(response):
        """Extract content from a streaming response."""
        content = ""
        try:
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if chunk.get("message", {}).get("content"):
                            content += chunk["message"]["content"]
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            log.error(f"Error extracting content from stream: {str(e)}")
            
        return content.strip() 