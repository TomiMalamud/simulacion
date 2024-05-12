from flask import Flask, render_template

def create_app():
    app = Flask(__name__)

    from .views import app_views
    app.register_blueprint(app_views)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404


    return app
