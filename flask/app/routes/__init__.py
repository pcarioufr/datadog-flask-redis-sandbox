import flask
from flask import current_app as app
from app.logs import log
from app.services.llm_service import LLMService

# Import all route modules
from . import auth
from . import chat
from . import config

@app.route("/")
def home():
    """Home page route."""
    user = auth.auth()
    return flask.render_template(
        "home.jinja",
        user_id=user.user_id,
        user_email=user.email,
        is_anonymous=False,
        clientToken=app.config["DD_CLIENT_TOKEN"],
        applicationId=app.config["DD_APPLICATION_ID"],
        dd_version=app.config["DD_VERSION"],
        dd_env=app.config["DD_ENV"],
        dd_site=app.config["DD_SITE"],
    )

@app.route("/api/ping")
def ping():
    """Health check endpoint."""
    log.info("ping successful")
    return flask.jsonify(response="pong"), 200

@app.route("/ui/ping")
def ui_ping():
    """UI health check endpoint that verifies Ollama status."""
    try:
        # Check if Ollama is running and has at least one model
        LLMService.check_ollama_status()
        return flask.jsonify({
            "status": "success",
            "message": "Ollama is running and ready"
        }), 200
    except ValueError as e:
        return flask.jsonify({
            "status": "error",
            "error": str(e)
        }), 503
    except Exception as e:
        log.error(f"Error in UI ping: {str(e)}")
        return flask.jsonify({
            "status": "error",
            "error": "Unexpected error checking Ollama status"
        }), 500 