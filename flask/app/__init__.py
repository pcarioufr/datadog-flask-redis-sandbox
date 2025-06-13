from flask import Flask
import redis
from ddtrace import tracer


@tracer.wrap()
def init_app():
    """Initialize and configure the Flask application."""
    app = Flask(__name__,
                static_url_path="/static",
                static_folder="./static",
                template_folder='./templates')
    app.config.from_object('config.Config')
    
    # Initialize Redis client
    app.redis_client = redis.Redis(
        host=app.config["REDIS_HOST"],
        decode_responses=True
    )
    
    # Import routes within app context
    with app.app_context():
        from . import routes
    
    return app
