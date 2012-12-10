import grequests
import json
import linecache
import os
import subprocess
import re
import redis

from collections import defaultdict
from itertools import cycle, izip
from flask import Flask, request, render_template, jsonify
from werkzeug.contrib.fixers import ProxyFix
from glob import glob
from gevent.pywsgi import WSGIServer
from os.path import basename, splitext

app = Flask(__name__)
app.debug = True

@app.route('/')
def index():
    fasta_genomes = [basename(genome) for genome
        in glob('/proj_data/genomes/*.fasta')]
    genomes = [splitext(genome)[0] for genome in fasta_genomes]
    gffs_withext = [basename(gff) for gff in glob('/proj_data/gff/*.gff')]
    gffs = [splitext(gff)[0] for gff in gffs_withext]
    return render_template('index.html', genomes=genomes, gffs=gffs)

@app.route('/gridview/<gff>')
def gridview(gff):
    full_gff = glob('/proj_data/gff/'+ gff + '.gff')
    if (len(full_gff)):
        full_gff = full_gff[0]
    return render_template('gridview.html', gff=gff, full_gff=full_gff)

@app.route('/gff/<gff>')
def gff_ajax(gff):
    offset = int(request.args.get('offset', 0))
    size = int(request.args.get('size', 40))

    full_gff = glob('/proj_data/gff/'+ gff + '.gff')
    if (len(full_gff)):
        full_gff = full_gff[0]

    data = {}
    data['offset'] = offset
    data['finished'] = False
    gff_data = []
    for i in range(offset+1, offset+size+1):
        line = linecache.getline(full_gff, offset + i)
        if line and not line.strip().startswith('#'):
            (seqid, feature, type, start, end, score,
            strand, phase, attributes) = line.split('\t')
            gff_data.append({
                'seqid': seqid,
                'feature': feature,
                'type': type,
                'start': start,
                'end': end,
                'score': score,
                'strand': strand,
                'phase': phase,
                'attributes': attributes,
            })
        elif not line:
            data['finished'] = True


    data['size'] = len(gff_data)
    data['gff'] = gff_data
    return json.dumps(data, indent=2)

@app.route('/chromosomes/<parent>')
def chromosomes(parent):
    chromos_gffs = (basename(chromosome) for chromosome
        in glob('/proj_data/chromosomes/%s*.fasta' % parent))
    chromos = [splitext(gff)[0] for gff in chromos_gffs]
    return render_template('chromosomes.html', parent=parent, chromosomes=chromos)

def unix_timestamp():
    import time
    return '%.3f' % time.time()

def unix_to_iso8601(timestamp):
    import datetime
    """Return unix `timestamp` converted to ISO8601: 2012-12-25T13:45:59Z"""
    utc = datetime.datetime.fromtimestamp(timestamp)
    return utc.strftime('%Y-%m-%dT%H:%M:%SZ')

@app.route('/register_worker', methods=['POST'])
def register_worker():
    assert 'hostname' in request.form
    hostname = request.form['hostname']

    # must be a hostname, please no pwning
    if len(re.findall(r'[.a-zA-Z\d-]+', hostname)) != 1:
        abort(400)

    r = redis.StrictRedis()
    key = 'worker:' + hostname
    now = unix_timestamp()
    r.hset(key, 'created', now)
    r.hset(key, 'last_pong', now)
    r.hset(key, 'initialized', False)

    PEM = os.environ.get('PEM', 'might-be-running-in-debug');
    # extra options disable known host additions
    p = subprocess.Popen(['ssh', '-i', PEM,
                                 '-o', 'UserKnownHostsFile=/dev/null',
                                 '-o', 'StrictHostKeyChecking=no',
                                 'ubuntu@' + hostname],
                                 stdin=subprocess.PIPE)
    with open('remote.sh') as f:
        p.stdin.write(f.read())

    return 'worker registered\n'

@app.route('/unregister_worker', methods=['POST'])
def unregister_worker():
    assert 'hostname' in request.form
    hostname = request.form['hostname']
    r = redis.StrictRedis()
    r.delete('worker:' + hostname)
    return 'worker unregistered\n'

@app.route('/update_worker', methods=['POST'])
def update_worker():
    assert 'hostname' in request.form
    hostname = request.form['hostname']
    r = redis.StrictRedis()
    r.hset('worker:' + hostname, 'last_pong', unix_timestamp())
    r.hset('worker:' + hostname, 'initialized', True)
    return 'worker updated\n'

@app.route('/workers')
def workers():
    r = redis.StrictRedis()
    response = {}
    for key in r.keys('worker:*'):
        response[key] = r.hgetall(key)
    return jsonify(response)

@app.route('/worker_info')
def worker_info():
    r = redis.StrictRedis()
    key = '/worker_info'
    cache = r.get(key)
    if cache:
        return cache
    else:
        response = defaultdict(dict)

        urls = []
        hosts = []
        info_list = []
        endpoints = ('os_name', 'memory_usage', 'disk_usage', 'cpu')
        for worker in r.keys('worker:*'):
            info = r.hgetall(worker)
            _, hostname = worker.split(':')
            for endpoint in endpoints:
                url = 'http://'+hostname+'/v0.9/' + endpoint
                hosts.append(hostname)
                urls.append(url)
                info_list.append(info)

        rs = (grequests.get(url, timeout=0.2) for url in urls)

        # this spews exceptions from greenlet, but is really fast, probably
        # need to dive into gevent/greenlets to solve
        for host, info, resp, endpoint in izip(hosts, info_list, grequests.map(rs),
            cycle(endpoints)):
            if resp.status_code == 200:
                response[host][endpoint] = resp.json
                if 'last_pong' in info:
                    response[host]['last_heartbeat'] = unix_to_iso8601(
                        float(info['last_pong']))
                if 'created' in info:
                    response[host]['created'] = info['created']

        json_response = json.dumps(response)
        r.set(key, json_response)
        r.expire(key, 1)
        return json_response

file_suffix_to_mimetype = {
    '.css': 'text/css',
    '.jpg': 'image/jpeg',
    '.html': 'text/html',
    '.ico': 'image/x-icon',
    '.png': 'image/png',
    '.js': 'application/javascript'
}

@app.route('/<path:path>')
def static_serve(path):
    import flask
    path = 'public/' + path
    if not app.debug:
        flask.abort(404)
    try:
        f = open(path)
    except IOError:
        flask.abort(404)
        return
    root, ext = splitext(path)
    if ext in file_suffix_to_mimetype:
        return flask.Response(f.read(), mimetype=file_suffix_to_mimetype[ext])
    return f.read()

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 80))
    http = WSGIServer((host, port), app)
    print 'Listening on %s:%d' % (host, port)
    http.serve_forever()
