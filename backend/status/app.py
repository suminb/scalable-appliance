from flask import Flask, jsonify
from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException
import psutil

# http://flask.pocoo.org/snippets/83/
def make_json_app(import_name, **kwargs):
    """
    Creates a JSON-oriented Flask app.

    All error responses that you don't specifically
    manage yourself will have application/json content
    type, and will contain JSON like this (just an example):

    { "message": "405: Method Not Allowed" }
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
app.secret_key = '74dc916419a178d22cb0fc8a04f62d345784ad7d'

@app.route('/')
def index():
    return jsonify(latest_version='0.9', support_versions=['0.9'])

@app.route('/v0.9/version')
def version():
    return jsonify(methods_supported=[
        'memory_usage',
        'disk_usage',
    ])

@app.route('/v0.9/memory_usage')
def memory_usage():
    memory = psutil.virtual_memory()
    status = {
        'total': memory.total,
        'available': memory.available,
        'used': memory.used,
        'free': memory.free,
        'active': memory.active,
        'inactive': memory.inactive,
        'percent': memory.percent,
    }
    return jsonify(status)

@app.route('/v0.9/disk_usage')
def disk_usage():
    partitions = psutil.disk_partitions()
    status = {}
    for partition in partitions:
        usage = psutil.disk_usage(partition.mountpoint)
        status[partition.device] = {
            'mountpoint': partition.mountpoint,
            'fstype': partition.fstype,
            'opts': partition.opts,
            'total': usage.total,
            'used': usage.used,
            'free': usage.free,
            'percent': usage.percent
        }
    return jsonify(status)

if __name__ == '__main__':
    import os
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 80))
    app.run(host=host, port=port, debug=True)
