from flask import Flask
from ddtrace import tracer

@tracer.wrap()
def init_app():

    app = Flask(__name__)

    with app.app_context():

        from .routes import hello_world, count

        return app
