import requests
from flask import current_app as app
import json
import logging
from app.logs import log
from ddtrace import tracer

log = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with the LLM."""
    
    OLLAMA_URL = f"{app.config['OLLAMA_HOST']}/api/chat"

    @staticmethod
    @tracer.wrap(service="ollama", name="generate_response_stream")
    def generate_response_stream(messages, system_prompt):
        """Generate a streaming response from the LLM."""
        
        # Prepare the request for Ollama with system prompt
        ollama_request = {
            "model": app.config["OLLAMA_MODEL"],
            "messages": ([{"role": "system", "content": system_prompt}] if system_prompt else []) + messages,
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
            LLMService.OLLAMA_URL,
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

    @staticmethod
    @tracer.wrap(service="ollama", name="generate_response_sync")
    def generate_response_sync(messages):
        """Get a synchronous (non-streaming) response from Ollama.
        
        Args:
            messages (list): List of message objects with role and content
        
        Returns:
            str: The model's response text
        """
        try:
            response = requests.post(LLMService.OLLAMA_URL, json={
                "model": app.config["OLLAMA_MODEL"],
                "messages": messages,
                "stream": False
            })
            response.raise_for_status()
            
            data = response.json()
            if "message" in data and "content" in data["message"]:
                return data["message"]["content"]
            else:
                raise ValueError("Unexpected response format from Ollama")
                
        except Exception as e:
            log.error(f"Error getting sync response from LLM: {str(e)}")
            raise 