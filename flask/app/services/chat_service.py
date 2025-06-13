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
        self.config_key = f"chat_config:{user.user_id}"
        self._config = None
        self.history = []
        
        # Always load history on initialization
        self.load_history()
        log.info(f"Initialized chat service for user {user.user_id}")
        
    @tracer.wrap(name="chat.load_history")
    def load_history(self):
        """Load chat history from storage and return if it exists."""
        history = self.redis_client.get(self.history_key)
        self.history = json.loads(history) if history else []
        return bool(self.history)
        
    @tracer.wrap(name="chat.save_history")
    def save_history(self):
        """Save chat history to storage."""
        self.redis_client.set(self.history_key, json.dumps(self.history))
        
    @tracer.wrap(name="chat.clear_history")
    def clear_history(self):
        """Clear chat history."""
        # Clear history only
        self.redis_client.delete(self.history_key)
        self.history = []
        log.info(f"Cleared history for user {self.user.user_id}")

    @tracer.wrap(name="chat.get_config")
    def get_config(self):
        """Get the current configuration (model and prompt)."""
        if self._config is None:
            # Try to get from storage
            config = self.redis_client.hgetall(self.config_key)
            if config:
                log.info(f"Loaded config from Redis for user {self.user.user_id}: model={config.get('model', '')}, prompt={config.get('prompt', '')[:50]}...")
                self._config = {
                    'model': config.get('model', ''),
                    'prompt': config.get('prompt', '')
                }
            else:
                log.error(f"No config set for user {self.user.user_id}")
                raise ValueError(f"No configuration set for user {self.user.user_id}. Please set model and prompt first.")
        return self._config
        
    @tracer.wrap(name="chat.set_config")
    def set_config(self, model=None, prompt=None):
        """Set new configuration values. Only updates provided values."""
        if self._config is None:
            self._config = {'model': '', 'prompt': ''}
            
        if model is not None:
            self._config['model'] = model.strip()
        if prompt is not None:
            self._config['prompt'] = prompt.strip()
            
        # Update Redis
        self.redis_client.hset(self.config_key, mapping={
            'model': self._config['model'],
            'prompt': self._config['prompt']
        })
        log.info(f"Updated config for user {self.user.user_id}")
        return self._config
        
    @tracer.wrap(name="chat.add_message")
    def add_message(self, content, role):
        """Add a message to history."""
        self.history.append({"role": role, "content": content})
        self.save_history()
        log.info(f"Added {role} message for user {self.user.user_id}, total messages: {len(self.history)}")
        
    @tracer.wrap(name="chat.process_message")
    def process_message(self, message_content):
        """Process a new message and return the response stream."""
        # Add user's message to history
        self.add_message(message_content, "user")
        
        # Get streaming response from LLM using current model
        return LLMService.generate_response_stream(self.history, self.get_config()['prompt'], self.get_config()['model'])
        
    @tracer.wrap(name="chat.get_welcome_message")
    def get_welcome_message(self):
        """Get a streaming welcome message."""
        return LLMService.generate_response_stream(
            [{"role": "user", "content": "Please provide a brief, welcoming message."}],
            self.get_config()['prompt'],
            self.get_config()['model']
        )

    @tracer.wrap(name="chat.initialize_chat")
    def initialize_chat_with_message(self, welcome_message):
        """Initialize chat with a provided welcome message."""
        log.info(f"Initializing chat for user {self.user.user_id}")
        self.history = []
        self.history.append({"role": "assistant", "content": welcome_message})
        self.save_history()
        return self.history 