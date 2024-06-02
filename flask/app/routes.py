import flask

from flask import current_app as app

import redis
import os

from app.logs import log

import random
import time


redis_client = redis.Redis(
            host=app.config["REDIS_HOST"],
            decode_responses=True
        )

def random_id():
    rid = ''.join((random.choice('1234567890abcdef') for i in range(8)))
    return rid


@app.route("/")
def hello_world():

    # Login when user_id is injected as a URL param 
    if flask.request.args.get("user_id") is not None:

        user_id = flask.request.args.get("user_id")

        flask.session["user_id"] = user_id
        flask.session["user_email"] = "{}@sandbox.com".format(user_id)

        log.info("user {} logged in".format(user_id))


    # Login as random user (when session cookie is empty)
    elif flask.session.get("user_id") is None:

        user_id = random_id()

        flask.session["user_id"] = user_id
        flask.session["user_email"] = "{}@sandbox.com".format(user_id)

        log.info("user {} logged in".format(user_id))

    # Recognizes an existing user (through session cookie)
    else:
        user_id = flask.session.get("user_id")


    if redis_client.get(user_id) is None:
        user_init_count = 0
    else:
        user_init_count = redis_client.get(user_id)

    return flask.render_template(
        "home.jinja",
        user_id=flask.session.get("user_id"),
        user_email=flask.session.get("user_email"),
        user_init_count=user_init_count,
        is_anonymous=False,
        clientToken=app.config["DD_CLIENT_TOKEN"],
        applicationId=app.config["DD_APPLICATION_ID"],
        dd_version=app.config["DD_VERSION"],
        dd_env=app.config["DD_ENV"],
        dd_site=app.config["DD_SITE"],
    )



@app.route("/count/<user_id>", methods=['GET', 'POST'])
def count(user_id=None):


    trace_id = flask.request.headers.get("X-Datadog-Trace-Id")
    parent_id = flask.request.headers.get("X-Datadog-Parent-Id")
    log.info("Parent: Trace ID {} - Span ID {}".format(trace_id, parent_id))

    if user_id is None:
        return flask.jsonify(), 400

    # adds random latency to the request
    r_lat = random.triangular(0, 2)
    time.sleep(r_lat)

    # random fails the query
    r_err = random.random()
    if r_err > 0.5 :
        log.error("oops")
        return flask.jsonify(), 500

    if flask.request.method == 'POST':
        redis_client.incr(user_id, 1)

    count = redis_client.get(user_id)
    log.info("count={}".format(count))

    return flask.jsonify(user_id=user_id, count=count)
