import flask
from flask import current_app as app
from app.logs import log

# Import all route modules
from . import auth
from . import chat
from . import prompt

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