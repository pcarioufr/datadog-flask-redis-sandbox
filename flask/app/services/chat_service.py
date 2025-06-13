import json
from app.logs import log
from .llm_service import LLMService
from ddtrace import tracer
from flask import current_app as app

class ChatService:
    """Service for handling chat operations."""
    
    @tracer.wrap(name="chat.initialize")
    def __init__(self, redis_client, user):
        """Initialize chat service and load history."""
        self.redis_client = redis_client
        self.user = user
        self.history_key = f"chat_history:{user.user_id}"
        self._system_prompt = None
        self.prompt_key = f"chat_prompt:{user.user_id}"
        self.model_key = f"chat_model:{user.user_id}"
        self._model = None
        self.history = []
        
        # Always load history on initialization
        self.load_history()
        log.info(f"Initialized chat service for user {user.user_id}")
        
    @tracer.wrap(name="chat.load_history")
    def load_history(self):
        """Load chat history from storage and return if it exists."""
        history = self.redis_client.get(self.history_key)
        self.history = json.loads(history) if history else []
        log.info(f"Loaded {len(self.history)} messages for user {self.user.user_id}")
        return bool(self.history)
        
    @tracer.wrap(name="chat.save_history")
    def save_history(self):
        """Save chat history to storage."""
        self.redis_client.set(self.history_key, json.dumps(self.history))
        log.info(f"Saved {len(self.history)} messages for user {self.user.user_id}")
        
    @tracer.wrap(name="chat.clear_history")
    def clear_history(self):
        """Clear chat history but preserve system prompt. Prepend system prompt as a system message if it exists."""
        # Clear history only
        self.redis_client.delete(self.history_key)
        self.history = []

        # Do NOT clear system prompt
        # self.redis_client.delete(self.prompt_key)
        # self._system_prompt = None

        # Prepend system prompt as a system message if it exists
        prompt = self.get_prompt()
        if prompt and prompt.strip():
            self.history.append({"role": "system", "content": prompt.strip()})
            self.save_history()

        log.info(f"Cleared history and prepended system prompt for user {self.user.user_id}")
        
    @tracer.wrap(name="chat.add_message")
    def add_message(self, content, role):
        """Add a message to history."""
        self.history.append({"role": role, "content": content})
        self.save_history()
        log.info(f"Added {role} message for user {self.user.user_id}, total messages: {len(self.history)}")
        
    @tracer.wrap(name="chat.get_prompt")
    def get_prompt(self):
        """Get the current system prompt."""
        if self._system_prompt is None:
            # Only try to get from storage, never load default
            prompt = self.redis_client.get(self.prompt_key)
            if prompt:
                log.info(f"Loaded system prompt from Redis for user {self.user.user_id}")
                self._system_prompt = prompt
            else:
                log.info(f"No system prompt set for user {self.user.user_id}")
                self._system_prompt = ""
        return self._system_prompt
        
    @tracer.wrap(name="chat.set_prompt")
    def set_prompt(self, new_prompt):
        """Set a new system prompt."""
        self._system_prompt = new_prompt.strip()
        self.redis_client.set(self.prompt_key, self._system_prompt)
        log.info(f"Updated system prompt for user {self.user.user_id}")
        return self._system_prompt
        
    @tracer.wrap(name="chat.get_model")
    def get_model(self):
        """Get the current model."""
        if self._model is None:
            # Try to get from storage
            model = self.redis_client.get(self.model_key)
            if model:
                log.info(f"Loaded model from Redis for user {self.user.user_id}")
                self._model = model
            else:
                log.info(f"No model set for user {self.user.user_id}, using default")
                self._model = app.config["OLLAMA_MODEL"]
        return self._model
        
    @tracer.wrap(name="chat.set_model")
    def set_model(self, new_model):
        """Set a new model."""
        self._model = new_model.strip()
        self.redis_client.set(self.model_key, self._model)
        log.info(f"Updated model to {self._model} for user {self.user.user_id}")
        return self._model
        
    @tracer.wrap(name="chat.process_message")
    def process_message(self, message_content):
        """Process a new message and return the response stream."""
        # Add user's message to history
        self.add_message(message_content, "user")
        
        # Get streaming response from LLM using current model
        return LLMService.generate_response_stream(self.history, self.get_prompt(), self.get_model())
        
    @tracer.wrap(name="chat.get_welcome_message")
    def get_welcome_message(self):
        """Get a streaming welcome message."""
        return LLMService.generate_response_stream(
            [{"role": "user", "content": "Please provide a brief, welcoming message."}],
            self.get_prompt(),
            self.get_model()
        )

    @tracer.wrap(name="chat.initialize_chat")
    def initialize_chat_with_message(self, welcome_message):
        """Initialize chat with a provided welcome message, prepending system prompt if it exists."""
        log.info(f"Initializing chat for user {self.user.user_id}")
        self.history = []
        prompt = self.get_prompt()
        if prompt and prompt.strip():
            self.history.append({"role": "system", "content": prompt.strip()})
        self.history.append({"role": "assistant", "content": welcome_message})
        self.save_history()
        return self.history 