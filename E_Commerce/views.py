from flask import *
from . import app

app.secret_key = 'random string'

@app.route('/', subdomain='homologacao')
def homologacao():
    return 'ok'

@app.route('/')
def hqq():
    return render_template('teste.html')