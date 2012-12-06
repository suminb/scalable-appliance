import json
import linecache
import subprocess
import re

from flask import Flask, request, render_template, jsonify
from werkzeug.contrib.fixers import ProxyFix
from glob import glob
from os.path import basename, splitext
import redis

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
    data['disclaimer'] = "I have no idea what version of GFF this data is, don't trust anything you see here"
    return json.dumps(data, indent=2)

@app.route('/chromosomes/<parent>')
def chromosomes(parent):
    chromos_gffs = (basename(chromosome) for chromosome
        in glob('/proj_data/chromosomes/%s*.fasta' % parent))
    chromos = [splitext(gff)[0] for gff in chromos_gffs]
    return render_template('chromosomes.html', parent=parent, chromosomes=chromos)

def utc_timestamp():
    """Return a current timestamp as ISO8601: 2012-12-25T13:45:59Z"""
    import datetime
    utc = datetime.datetime.utcnow()
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
    now = utc_timestamp()
    r.hset(key, 'created', now)
    r.hset(key, 'last_pong', now)

    p_in = subprocess.Popen(["ssh", "-i", "/home/charlesl/monitoring-test.pem",
        "ubuntu@" + hostname], stdin=subprocess.PIPE).stdin
    with open('remote.sh') as f:
        p_in.communicate(input=f.read())

    return 'worker registered\n'

@app.route('/update_worker', methods=['POST'])
def update_worker():
    assert 'hostname' in request.form
    hostname = request.form['hostname']
    r = redis.StrictRedis()
    r.hset('worker:' + hostname, 'last_pong', utc_timestamp())
    return 'worker updated\n'

@app.route('/workers')
def workers():
    r = redis.StrictRedis()
    response = {}
    for key in r.keys('worker:*'):
        response[key] = r.hgetall(key)
    return jsonify(response)

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
    import os
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 80))
    app.run(host=host, port=port)
