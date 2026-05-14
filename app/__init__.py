from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager # NEW
import os
from authlib.integrations.flask_client import OAuth # NEW
from config import Config
from supabase import create_client, Client # NEW

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)         # NEW
login.login_view = 'login'        # NEW: Redirects here if they try to access a protected page
oauth = OAuth(app)                # NEW

# NEW: Supabase Initialization
url: str = app.config.get("SUPABASE_URL")
key: str = app.config.get("SUPABASE_KEY")
if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the environment.")

supabase: Client = create_client(url, key)
app.config['SUPABASE_CLIENT'] = supabase
app.config['SUPABASE_BUCKET'] = "product-images" # The bucket name you created

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
# NEW: Add image base URL to Jinja2 templates
image_base_url = f"{url}/storage/v1/object/public/{app.config['SUPABASE_BUCKET']}"
app.jinja_env.globals.update(len=len, IMAGE_BASE_URL=image_base_url)


from app import routes, models # noqa