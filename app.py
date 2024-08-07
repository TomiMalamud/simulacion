from flask import Flask, render_template
from app.tp2 import tp2
from app.tp3 import tp3
from app.tp4 import tp4
from app.tp5 import tp5

app = Flask(__name__, template_folder="app/templates", static_folder="app/static")

app.register_blueprint(tp2)
app.register_blueprint(tp3)
app.register_blueprint(tp4)
app.register_blueprint(tp5)

@app.route("/")
def index():
    return render_template("index.html")


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
