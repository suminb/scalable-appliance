__author__ = "Sumin Byeon <suminb@gmail.com>"

from flask import Flask, jsonify
from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException

import util
import json

__all__ = ['make_json_app']

def make_json_app(import_name, **kwargs):
    """
    Creates a JSON-oriented Flask app.

    All error responses that you don't specifically
    manage yourself will have application/json content
    type, and will contain JSON like this (just an example):

    { "message": "405: Method Not Allowed" }

    http://flask.pocoo.org/snippets/83/
    """
    def make_json_error(ex):
        response = jsonify(message=str(ex))
        response.status_code = (ex.code
                                if isinstance(ex, HTTPException)
                                else 500)
        return response

    app = Flask(import_name, **kwargs)

    for code in default_exceptions.iterkeys():
        app.error_handler_spec[None][code] = make_json_error

    return app

app = make_json_app(__name__)


@app.route('/')
def index():
    return jsonify(latest_version='0.9', support_versions=['0.9'])

@app.route('/v0.9/ping')
def ping():
    return "pong"

@app.route('/v0.9/status')
    return ""

@app.route('/v0.9/memory_usage')
def memory_usage():
    payload = util.memory_usage()
    return json.dumps(payload)

@app.route('/v0.9/disk_usage')
def disk_usage():
    payload = util.disk_usage()
    return json.dumps(payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0")