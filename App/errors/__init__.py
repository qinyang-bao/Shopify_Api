from flask import Blueprint

bp = Blueprint('errors', __name__)

from App.errors import handlers