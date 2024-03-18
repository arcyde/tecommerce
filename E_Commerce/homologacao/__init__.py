from flask import *

homologacao = Blueprint(
    'homologacao',
    __name__,
    template_folder='templates',
    static_folder='static'
)

from . import views