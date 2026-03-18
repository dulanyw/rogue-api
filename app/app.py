from flask import Flask
from .config import Config
from .api.routes import bp

def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    
    if config:
        app.config.update(config)
    
    app.register_blueprint(bp)
    return app
