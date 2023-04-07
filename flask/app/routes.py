import flask

from flask import current_app as app

import redis
import os

from app.logs import log

import random


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



@app.route("/count/<key>", methods=['GET', 'POST'])
def count(key=None):

    if key is None:
        return flask.jsonify(), 400

    if flask.request.method == 'POST':
        redis_client.incr(key, 1)

    count = redis_client.get(key)
    log.info("count={}".format(count))

    return flask.jsonify(key=key, count=count)


@app.route("/broken", methods=['GET'])
def broken():

    r = random.random()

    if r > 0.5 :
        log.error("oops")
        return flask.jsonify(), 500

    return flask.jsonify(), 204
