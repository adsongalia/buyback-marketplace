from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os
from authlib.integrations.flask_client import OAuth
from config import Config
from supabase import create_client, Client

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
oauth = OAuth()

login.login_view = 'main.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    oauth.init_app(app)

    # Supabase Initialization
    url: str = app.config.get("SUPABASE_URL")
    key: str = app.config.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the environment.")

    supabase: Client = create_client(url, key)
    app.config['SUPABASE_CLIENT'] = supabase
    app.config['SUPABASE_BUCKET'] = "product-images"

    oauth.register(
        name='google',
        client_id=app.config.get("GOOGLE_CLIENT_ID"),
        client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    # Add image base URL to Jinja2 templates
    image_base_url = f"{url}/storage/v1/object/public/{app.config['SUPABASE_BUCKET']}"
    app.jinja_env.globals.update(len=len, IMAGE_BASE_URL=image_base_url)

    from app.routes import bp as main_blueprint
    app.register_blueprint(main_blueprint)

    return app

from app import models