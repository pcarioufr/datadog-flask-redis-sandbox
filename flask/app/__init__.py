from flask import Flask
from ddtrace import tracer
import redis


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

    with app.app_context():
        # Import routes which will register all endpoints
        from . import routes
        return app
