import random
import flask
from app.logs import log

class User:
    """User class for handling user data and session management."""
    
    def __init__(self, user_id=None):
        """Initialize user with optional user_id."""
        self.user_id = user_id or self._generate_random_id()
        self.email = f"{self.user_id}@sandbox.com"

    @staticmethod
    def _generate_random_id():
        """Generate a random user ID."""
        return ''.join(random.choice('1234567890abcdef') for _ in range(8))

    @classmethod
    def from_session(cls):
        """Create a User instance from the current session."""
        user_id = flask.session.get("user_id")
        return cls(user_id) if user_id else None

    def login(self):
        """Log in the user by setting session data."""
        flask.session["user_id"] = self.user_id
        flask.session["user_email"] = self.email
        log.info(f"user {self.user_id} logged in") 