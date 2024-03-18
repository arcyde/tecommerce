"""
The flask application package.
"""
from flask import *
from .homologacao import homologacao

app = Flask(__name__)

app.register_blueprint(homologacao, subdomain='homologacao')

import E_Commerce.views
