from App.main import bp
from flask import render_template


@bp.route("/")
@bp.route("/documentation")
def index():
    return render_template("documentation.html")


