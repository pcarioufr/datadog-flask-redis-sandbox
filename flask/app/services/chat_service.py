import json
from app.logs import log
from .llm_service import LLMService
from ddtrace import tracer
from flask import current_app as app
from ddtrace.llmobs import LLMObs


class ChatService:
    """Base class for chat services."""
    
    def __init__(self, model: str = None, prompt: str = None):
        """Initialize the base chat service.
        
        Args:
            model: Name of the Ollama model to use
            prompt: Optional system prompt to use
        """
        if self.__class__ == ChatService:
            raise TypeError("ChatService is an abstract class and cannot be instantiated directly")
            
        # Check Ollama status first
        LLMService.check_ollama_status()
        
        # Initialize LLM service if model is provided
        self.llm_service = LLMService(model=model, prompt=prompt) if model else None
    
    def process_message(self, messages):
        """Process a message and return the response."""
        if not self.llm_service:
            raise RuntimeError("LLM service not initialized")
        return self.llm_service.generate_response_sync(messages)
    
    def process_message_stream(self, messages):
        """Process a message and return the streaming response.
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            requests.Response: The raw streaming response from Ollama
        """
        if not self.llm_service:
            raise RuntimeError("LLM service not initialized")
            
        return self.llm_service.generate_response_stream(messages)


class StatelessChatService(ChatService):
    """Service for handling chat requests without state persistence."""
    pass


class StatefulChatService(ChatService):
    """Service for handling chat requests with state persistence."""
    
    @classmethod
    def exists(cls, user_id):
        """Check if a chat exists for the given user.
        
        Args:
            user_id: User ID to check
            
        Returns:
            bool: True if chat exists, False otherwise
        """
        config_key = f"chat_config:{user_id}"
        return bool(app.redis_client.exists(config_key))
    
    @classmethod
    def create(cls, user, model, prompt):
        """Create a new chat service with initial config.
        
        Args:
            user: User instance
            model: Initial model to use
            prompt: Initial prompt to use
            
        Returns:
            StatefulChatService: New service instance
        """
        instance = cls.__new__(cls)
        instance.user = user
        instance.history_key = f"chat_history:{user.user_id}"
        instance.config_key = f"chat_config:{user.user_id}"
        instance.history = []
        # Validate and prepare config (consistent with set_config validation)
        model = model.strip() if model else ""
        prompt = prompt.strip() if prompt else ""
        
        if not model:
            raise ValueError("Model cannot be empty")
            
        instance.config = {'model': model, 'prompt': prompt}
        
        # Save initial config
        app.redis_client.hset(instance.config_key, mapping=instance.config)
        
        # Initialize base class
        super(StatefulChatService, instance).__init__(
            model=instance.config['model'],
            prompt=instance.config['prompt']
        )
        
        log.info(f"Created new chat service for user {instance.user.user_id}")
        return instance
    
    @tracer.wrap(name="chat.initialize")
    def __init__(self, user):
        """Initialize chat service and load state."""
        
        self.user = user
        self.history_key = f"chat_history:{user.user_id}"
        self.config_key = f"chat_config:{user.user_id}"
        
        # Load history
        history = app.redis_client.get(self.history_key)
        self.history = json.loads(history) if history else []
        
        # Load config
        config = app.redis_client.hgetall(self.config_key)
        if not config:
            log.error(f"No config set for user {self.user.user_id}")
            raise ValueError(f"No configuration set for user {self.user.user_id}. Please set model and prompt first.")
            
        self.config = {
            'model': config.get('model', ''),
            'prompt': config.get('prompt', '')
        }
        log.info(f"Loaded config from Redis for user {self.user.user_id}: model={self.config['model']}, prompt={self.config['prompt'][:50]}...")
        
        # Initialize base class with loaded config
        super().__init__(model=self.config['model'], prompt=self.config['prompt'])
        
        log.info(f"Initialized chat service for user {self.user.user_id}")

    @tracer.wrap(name="chat.clear_history")
    def clear_history(self):
        """Clear chat history."""
        app.redis_client.delete(self.history_key)
        self.history = []
        log.info(f"Cleared history for user {self.user.user_id}")

    @tracer.wrap(name="chat._add_message")
    def _add_message(self, content, role):
        """Add a message to history and persist it."""
        self.history.append({"role": role, "content": content})
        app.redis_client.set(self.history_key, json.dumps(self.history))
        log.info(f"Added {role} message for user {self.user.user_id}, total messages: {len(self.history)}")

    @tracer.wrap(name="chat.set_config")
    def set_config(self, model=None, prompt=None):
        """Set new configuration values. Only updates provided values.
        
        Args:
            model: Model name to set (will be stripped of whitespace)
            prompt: System prompt to set (will be stripped of whitespace)
            
        Returns:
            dict: Updated configuration
            
        Raises:
            ValueError: If model or prompt are empty strings after stripping
        """
        if model is not None:
            model = model.strip()
            if not model:
                raise ValueError("Model cannot be empty")
            self.config['model'] = model
            
        if prompt is not None:
            prompt = prompt.strip()
            # Allow empty prompt (user might want no system prompt)
            self.config['prompt'] = prompt
            
        # Update Redis
        app.redis_client.hset(self.config_key, mapping=self.config)
        
        # Reinitialize LLM service with new config
        self.llm_service = LLMService(model=self.config['model'], prompt=self.config['prompt'])
        
        log.info(f"Updated config for user {self.user.user_id}")
        return self.config

    def _create_cleanup_callback(self, input_messages):
        """Create a cleanup callback for handling persistence and telemetry.
        
        Args:
            input_messages: The messages that were sent to the LLM
            
        Returns:
            callable: Cleanup callback function
        """
        
        def cleanup_callback(complete_response):
            """Handle persistence and telemetry after streaming completes."""
            try:
                # Handle LLM observability telemetry
                with LLMObs.llm(model_name=self.config['model'], model_provider="ollama") as span:
                    LLMObs.annotate(
                        span=span,
                        input_data=input_messages,
                        output_data={"role": "assistant", "content": complete_response}
                    )
                
                # Persist the assistant's response
                self._add_message(complete_response, "assistant")
                log.info(f"Persisted complete response ({len(complete_response)} chars)")
                
            except Exception as e:
                log.error(f"Error in cleanup callback: {str(e)}")
        
        return cleanup_callback

    @tracer.wrap(name="chat.process_message_stream")
    def process_message_stream(self, message_content):
        """Process a new message and return the streaming response with cleanup callback.
        
        Args:
            message_content: The message to process
            
        Returns:
            tuple: (requests.Response, cleanup_callback)
                - requests.Response: The raw streaming response from Ollama
                - cleanup_callback: Function to call with complete response for persistence/telemetry
        """
        # Add user's message to history
        self._add_message(message_content, "user")
        log.info(f"Added user message to history: {message_content[:50]}...")
        
        # Get streaming response from LLM using history
        response = super().process_message_stream(self.history)
        
        # Create cleanup callback
        cleanup_callback = self._create_cleanup_callback(self.history)
        
        return response, cleanup_callback
        
    @tracer.wrap(name="chat.get_welcome_message_stream")
    def get_welcome_message_stream(self):
        """Get a streaming welcome message with cleanup callback.
        
        Returns:
            tuple: (requests.Response, cleanup_callback)
        """
        # Define welcome message
        welcome_messages = [{"role": "user", "content": "Please provide a brief, welcoming message."}]
        
        # Get streaming response from LLM
        response = super().process_message_stream(welcome_messages)
        
        # Create cleanup callback (note: welcome prompt is not persisted in history)
        cleanup_callback = self._create_cleanup_callback(welcome_messages)
        
        return response, cleanup_callback 