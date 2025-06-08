import json
from app.logs import log
from .llm_service import LLMService
from ddtrace import tracer

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
        """Clear chat history."""
        self.redis_client.delete(self.history_key)
        self.history = []
        log.info(f"Cleared history for user {self.user.user_id}")
        
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
            # Try to get from storage first
            prompt = self.redis_client.get(self.prompt_key)
            if prompt:
                self._system_prompt = prompt
            else:
                # Load default prompt from file
                try:
                    with open('/flask/default_prompt.txt', 'r') as f:
                        self._system_prompt = f.read().strip()
                        # Store for future use
                        self.redis_client.set(self.prompt_key, self._system_prompt)
                    log.info("Loaded default system prompt successfully")
                except Exception as e:
                    log.warning(f"Failed to load system prompt: {e}")
                    self._system_prompt = "You are a helpful AI assistant."
        return self._system_prompt
        
    @tracer.wrap(name="chat.set_prompt")
    def set_prompt(self, new_prompt):
        """Set a new system prompt."""
        self._system_prompt = new_prompt.strip()
        self.redis_client.set(self.prompt_key, self._system_prompt)
        log.info(f"Updated system prompt for user {self.user.user_id}")
        return self._system_prompt
        
    @tracer.wrap(name="chat.process_message")
    def process_message(self, message_content):
        """Process a new message and return the response stream."""
        # Add user's message to history
        self.add_message(message_content, "user")
        
        # Get streaming response from LLM
        return LLMService.generate_response_stream(self.history, self.get_prompt())
        
    @tracer.wrap(name="chat.get_welcome_message")
    def get_welcome_message(self):
        """Get a streaming welcome message."""
        return LLMService.generate_response_stream(
            [{"role": "user", "content": "Please provide a brief, welcoming message."}],
            self.get_prompt()
        )

    @tracer.wrap(name="chat.initialize_chat")
    def initialize_chat_with_message(self, welcome_message):
        """Initialize chat with a provided welcome message."""
        log.info(f"Initializing chat for user {self.user.user_id}")
        self.history = [
            {"role": "assistant", "content": welcome_message}
        ]
        self.save_history()
        return self.history 