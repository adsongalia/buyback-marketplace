from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager # NEW
import os # NEW
from authlib.integrations.flask_client import OAuth # NEW
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# NEW: Configuration for file uploads and folder creation
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)         # NEW
login.login_view = 'login'        # NEW: Redirects here if they try to access a protected page
oauth = OAuth(app)                # NEW

oauth.register(                   # NEW
    name='google',
    client_id=app.config.get("GOOGLE_CLIENT_ID"),
    client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# NEW: Make len() function available in Jinja2 templates
app.jinja_env.globals.update(len=len)

from app import routes, models # noqa