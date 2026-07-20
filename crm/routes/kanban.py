from flask import Blueprint, render_template

kanban_bp = Blueprint("kanban", __name__)


@kanban_bp.route("/kanban")
def kanban():
    return render_template("kanban.html")
