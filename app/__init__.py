from flask import Flask
from config import Config
from datetime import datetime

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from app import routes
    app.register_blueprint(routes.main)

    @app.template_filter('datetime')
    def format_datetime(value):
        return datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')

    return app
