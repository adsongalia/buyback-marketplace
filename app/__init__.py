from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os
from werkzeug.middleware.proxy_fix import ProxyFix
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
    
    # Important for Vercel: Ensures url_for(_external=True) generates HTTPS URLs for Google OAuth
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

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

    # Make len() available in Jinja2 templates
    app.jinja_env.globals.update(len=len)

    from app.routes import bp as main_blueprint
    app.register_blueprint(main_blueprint)

    return app

from app import models