from flask import Flask, request, render_template
from werkzeug.contrib.fixers import ProxyFix
from glob import glob
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
    gff = glob('/proj_data/gff/'+ gff + '.gff')
    if (len(gff)):
        gff = gff[0]
    return render_template('gridview.html', gff=gff)

@app.route('/chromosomes/<parent>')
def chromosomes(parent):
    chromos_gffs = (basename(chromosome) for chromosome
        in glob('/proj_data/chromosomes/%s*.fasta' % parent))
    chromos = [splitext(gff)[0] for gff in chromos_gffs]
    return render_template('chromosomes.html', parent=parent, chromosomes=chromos)

@app.route('/register_worker/', methods=['POST'])
def register_worker():
    return 'Register: name is ' + request.form['name'] + '\n'

@app.route('/update_worker/', methods=['POST'])
def update_worker():
    return 'Update: name is ' + request.form['name'] + '\n'

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run()
