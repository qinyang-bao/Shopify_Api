from App import db
from App.errors import bp
from flask import jsonify


@bp.app_errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "resource not found"}), 404


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "internal server error, an administrator has been notified. Sorry for the inconvenience"})\
        , 500
