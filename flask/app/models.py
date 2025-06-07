import random
import json
import requests
import flask
from flask import current_app as app
import redis
from app.logs import log

# Datadog LLM Observability
from ddtrace.llmobs import LLMObs
from ddtrace.llmobs.decorators import llm

redis_client = redis.Redis(
            host=app.config["REDIS_HOST"],
            decode_responses=True
        )

class User:
    def __init__(self, user_id=None):
        """Initialize user with optional user_id"""
        self.user_id = user_id or self._generate_random_id()
        self.email = f"{self.user_id}@sandbox.com"

    @staticmethod
    def _generate_random_id():
        """Generate a random user ID"""
        return ''.join(random.choice('1234567890abcdef') for _ in range(8))

    @classmethod
    def from_session(cls):
        """Create a User instance from the current session"""
        user_id = flask.session.get("user_id")
        return cls(user_id) if user_id else None

    def login(self):
        """Log in the user by setting session data"""
        flask.session["user_id"] = self.user_id
        flask.session["user_email"] = self.email
        log.info(f"user {self.user_id} logged in")


class Chat:
    
    def __init__(self, user):
        """Initialize chat for a user"""
        self.user = user
        self.history = []
        self.redis_key = f"chat_history:{user.user_id}"
        self._system_prompt = None
        self._load()

    def _init_chat(self):
        """Initialize chat with a welcome message from LLM"""
        welcome_prompt = "Please provide a brief, welcoming message to start our conversation."
        welcome_message = self._llm_call([{"role": "user", "content": welcome_prompt}])
        self.history = [
            {"role": "assistant", "content": welcome_message}
        ]
        self._save()
        return self.history

    def _load(self):
        """Load chat history from Redis"""
        history = redis_client.get(self.redis_key)
        if history:
            self.history = json.loads(history)
        else:
            # Initialize with assistant's welcome message from LLM
            self._init_chat()
        return self.history

    def _save(self):
        """Save chat history to Redis"""
        redis_client.set(self.redis_key, json.dumps(self.history))

    def _add_message(self, content, role="user"):
        """Add a message to the history"""
        self.history.append({"role": role, "content": content})
        self._save()

    def get_history(self):
        """Get the current chat history"""
        return self.history
        
    def delete_history(self):
        """Delete chat history and reinitialize with welcome message"""
        redis_client.delete(self.redis_key)
        return self._init_chat()

    def process_message(self, message_content):
        """Process a new message and return the assistant's response"""
        # Add user's message to history
        self._add_message(message_content, "user")
        
        # Get response from LLM
        assistant_response = self._llm_call(self.history)
        
        # Add assistant's response to history
        self._add_message(assistant_response, "assistant")
        
        # Clean up history by removing any empty messages
        self.history = [msg for msg in self.history if msg.get('content', '').strip()]
        self._save()
        
        return assistant_response

    @llm(model_name=app.config["OLLAMA_MODEL"], model_provider="ollama")
    def _llm_call(self, messages):
        """Make a call to Ollama API with proper Datadog tracing."""
        
        # Load the system prompt if not already loaded
        if self._system_prompt is None:
            try:
                with open('/flask/prompt.txt', 'r') as f:
                    self._system_prompt = f.read().strip()
                log.info("Loaded system prompt successfully")
            except Exception as e:
                log.warning(f"Failed to load system prompt: {e}")
                self._system_prompt = "You are a helpful AI assistant."

        # Prepare the request for Ollama with system prompt
        ollama_request = {
            "model": app.config["OLLAMA_MODEL"],
            "messages": [
                {"role": "system", "content": self._system_prompt}
            ] + messages,
            "stream": False,  # Disable streaming to get a single response
            "options": {
                "temperature": app.config["OLLAMA_TEMPERATURE"],
                "top_p": app.config["OLLAMA_TOP_P"]
            }
        }

        # Forward the request to Ollama    
        ollama_response = requests.post(
            'http://host.docker.internal:11434/api/chat',
            json=ollama_request
        )

        try:
            response_data = ollama_response.json()

        except json.JSONDecodeError as e:
            log.error(f"Failed to parse Ollama response: {ollama_response.text}")
            raise

        LLMObs.annotate(
            input_data=messages,
            output_data=response_data["message"]
        )

        # Extract and return the assistant's response
        assistant_response = response_data.get('message', {}).get('content', '').strip()
        if not assistant_response:
            log.warning("Received empty response from Ollama")
            raise ValueError("Received empty response from Ollama")
            
        return assistant_response 