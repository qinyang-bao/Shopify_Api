from flask import Blueprint

bp = Blueprint('main', __name__)

from App.main import routes

