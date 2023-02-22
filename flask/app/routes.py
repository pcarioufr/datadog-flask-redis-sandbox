import flask

from flask import current_app as app

import redis
import os

from app.logs import log

redis_client = redis.Redis(
            host=os.environ.get("REDIS_HOST"),
            decode_responses=True
        )

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/count/<key>", methods=['GET', 'POST'])
def count(key=None):

    if key is None:
        return flask.jsonify(), 400

    if flask.request.method == 'POST':
        redis_client.incr(key, 1)

    count = redis_client.get(key)
    log.info("count={}".format(count))

    return flask.jsonify(key=key, count=count)
