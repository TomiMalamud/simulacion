from flask import Blueprint, render_template, request, jsonify
import random

tp4 = Blueprint('tp4', __name__, template_folder='templates')

@tp4.route("/tp4")
def tp4_render():
    return render_template("tp4.html")
