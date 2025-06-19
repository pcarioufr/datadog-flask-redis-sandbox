import requests
from flask import current_app as app
from app.logs import log
from ddtrace import tracer
import os


class LLMService:
    """Service for interacting with the LLM."""
    
    OLLAMA_HOST = os.getenv('OLLAMA_HOST')

    @classmethod
    @tracer.wrap(service="ollama")
    def get_available_models(cls):
        """Get list of available models from Ollama."""
        try:
            response = requests.get(f"{cls.OLLAMA_HOST}/api/tags")
            if response.status_code != 200:
                raise ValueError("Failed to fetch available models")
            return [model['name'] for model in response.json().get('models', [])]
        except Exception as e:
            raise ValueError(f"Failed to fetch available models: {str(e)}")
    
    @classmethod
    @tracer.wrap(service="ollama")
    def check_ollama_status(cls):
        """Check if Ollama is running and has at least one model.
        
        Raises:
            ValueError: If Ollama is not running or has no models
        """
        # Test error simulation
        if app.config['TEST_OLLAMA_DOWN']:
            log.warning("TEST MODE: Simulating Ollama being down")
            raise ValueError("Cannot connect to Ollama, please make sure it's running.\n\nInstall [Ollama](https://ollama.com), and run `ollama serve`")
            
        if app.config['TEST_OLLAMA_NOMODEL']:
            log.warning("TEST MODE: Simulating no models available in Ollama")
            raise ValueError("**No models available**\n\nPlease install a model first. For example:\n\n`ollama pull mistral`")
            
        try:
            # First check if Ollama is running
            response = requests.get(f"{cls.OLLAMA_HOST}/api/tags")
            if response.status_code != 200:
                raise ValueError("**Ollama is not responding**\n\nPlease make sure Ollama is running with `ollama serve`")
            
            # Then check if there are any models
            models = response.json().get('models', [])
            if not models:
                raise ValueError("**No models available**\n\nPlease install a model first. For example:\n\n`ollama pull mistral`")
                
        except requests.exceptions.ConnectionError:
            raise ValueError("Cannot connect to Ollama, please make sure it's running.\n\nInstall [Ollama](https://ollama.com), and run `ollama serve`")
        except Exception as e:
            raise ValueError(f"**Error checking Ollama status**\n\n{str(e)}\n\nPlease check your Ollama installation.")
    
    def __init__(self, model: str, prompt: str = None):
        """Initialize the LLM service and validate the model.
        
        Args:
            model: Name of the Ollama model to use
            prompt: System prompt to use for all requests. If None, no system prompt will be used.
            
        Raises:
            ValueError: If Ollama is not running or has no models
        """
        # Check Ollama status
        self.check_ollama_status()
            
        self.model = model
        self.prompt = prompt
        self.url = f"{self.OLLAMA_HOST}/api/chat"

    @tracer.wrap(service="ollama")
    def generate_response_stream(self, messages):
        """Generate a streaming response from the LLM."""
        try:
            # Prepare messages with system prompt if it exists
            if self.prompt:
                messages = [{"role": "system", "content": self.prompt}] + messages

            # Prepare the request for Ollama
            ollama_request = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": app.config["OLLAMA_TEMPERATURE"],
                    "top_p": app.config["OLLAMA_TOP_P"],
                    "num_predict": int(app.config.get("OLLAMA_NUM_PREDICT")),
                    "num_ctx": int(app.config.get("OLLAMA_NUM_CTX"))
                }
            }

            log.info(f"Making Ollama API call with model: {self.model}, using system prompt: {self.prompt}")

            # Forward the request to Ollama    
            response = requests.post(
                f"{self.OLLAMA_HOST}/api/chat",
                json=ollama_request,
                stream=True
            )
            if response.status_code != 200:
                raise ValueError(f"Failed to generate response: {response.text}")
            return response
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to generate response: {str(e)}")

    @tracer.wrap(service="ollama")
    def generate_response_sync(self, messages):
        """Get a synchronous (non-streaming) response from Ollama.
        
        Args:
            messages (list): List of message objects with role and content
        
        Returns:
            str: The model's response text
        """
        try:
            # Prepare messages with system prompt if it exists
            if self.prompt:
                messages = [{"role": "system", "content": self.prompt}] + messages

            log.info(f"Making Ollama API call with model: {self.model}, using system prompt: {self.prompt}")

            # Prepare the request for Ollama
            ollama_request = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": app.config["OLLAMA_TEMPERATURE"],
                    "top_p": app.config["OLLAMA_TOP_P"],
                    "num_predict": int(app.config.get("OLLAMA_NUM_PREDICT")),
                    "num_ctx": int(app.config.get("OLLAMA_NUM_CTX"))
                }
            }

            response = requests.post(
                f"{self.OLLAMA_HOST}/api/chat",
                json=ollama_request
            )
            
            if response.status_code == 404:
                # Model not found, get available models
                try:
                    available_models = self.get_available_models()
                    raise ValueError(f"Model '{self.model}' not found. Available models: {', '.join(available_models)}")
                except ValueError as e:
                    raise ValueError(f"Model '{self.model}' not found and {str(e)}")
            
            response.raise_for_status()
            
            data = response.json()
            if "message" in data and "content" in data["message"]:
                return data["message"]["content"]
            else:
                raise ValueError("Unexpected response format from Ollama")
                
        except Exception as e:
            log.error(f"Error getting sync response from LLM: {str(e)}")
            raise 