from flask import Flask, render_template
from app.tp2 import tp2
from app.tp3 import tp3
from app.tp4 import tp4
from app.tp5 import tp5
from app.final import final
from app.runge_kutta import ode_solver_bp

app = Flask(__name__, template_folder="app/templates", static_folder="app/static")

app.register_blueprint(tp2)
app.register_blueprint(tp3)
app.register_blueprint(tp4)
app.register_blueprint(tp5)
app.register_blueprint(final)
app.register_blueprint(ode_solver_bp)

@app.route("/")
def index():
    return render_template("tp-final.html")


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
