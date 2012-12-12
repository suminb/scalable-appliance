from flask import Flask, jsonify
from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException
import psutil
import subprocess
import os
import re

# Configuration file
import config

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
        'os_name',
        'memory_usage',
        'disk_usage',
        'cpu',
    ])

@app.route('/v0.9/os_name')
def os_name():
    return jsonify({'os_name':subprocess.check_output(("uname", "-a"))})

@app.route('/v0.9/cpu')
def cpu():
    percents = psutil.cpu_percent(percpu=True)
    response = {}
    for cpu, percent in enumerate(percents):
        response['cpu-%d' % cpu] = percent
    return jsonify(response)

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

@app.route('/v0.9/worker_status')
def worker_status():
    log_file_path = os.path.join(config.WORKER_BASE_DIR, config.WORKER_LOG)
    if os.path.exists(log_file_path):
        workers = []

        # FIXME: Poor code readability
        worker_dirs = filter(lambda x: re.match(r'worker-\d+-\d+', x), [m for m in os.listdir(config.WORKER_BASE_DIR)])

        for dir_name in worker_dirs:
            worker_dir = os.path.join(config.WORKER_BASE_DIR, dir_name)
            files = [m for m in os.listdir(worker_dir)]

            worker_info = {
                'base_path': worker_dir,
                'files': files,
            }

            workers.append(worker_info)

        log = subprocess.check_output(("tail", "-n %d" % config.TAIL_LINES, log_file_path))
        return jsonify(worker_log=log, workers=workers)
    else:
        return jsonify(status='worker.log file does not exist.')

@app.route('/v0.9/log/<worker_name>/<file_name>')
def tail(worker_name, file_name):
    # TODO: This may lead to some security vulnerabilities
    file_path = os.path.join(config.WORKER_BASE_DIR, worker_name, file_name)

    if os.path.exists(file_path):
        log = subprocess.check_output(("tail", "-n %d" % config.TAIL_LINES, file_path))

        return jsonify(log=log)
    else:
        return jsonify(status='Requested log file does not exist.')

if __name__ == '__main__':
    import os
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 80))
    app.run(host=host, port=port, debug=True)
