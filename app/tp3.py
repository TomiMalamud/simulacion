from flask import Blueprint, render_template, request, jsonify

tp3 = Blueprint('tp3', __name__, template_folder='templates')

@tp3.route("/tp3")
def tp3_render():
    return render_template("tp3.html")