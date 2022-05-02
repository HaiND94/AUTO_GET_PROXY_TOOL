from flask import Flask
from .config import Config
from flask_pymongo import PyMongo
from flask_cors import CORS, cross_origin

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager

import redis
import logging

# Config logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log_file.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Config redis
r = redis.Redis(host='localhost', port=6379, db=10)

# Init app
app = Flask(__name__)
# login = LoginManager(app)
app.config.from_object(Config)

# Set CORS for app
CORS(app)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["4000 per day", "200 per hour"]
)

# Config and init for database
mongo1 = PyMongo(app, uri="mongodb://localhost:27017/Vfastdatabase")
users_table = mongo1.db.users

# Init login
login = LoginManager(app)
login.login_view = 'login'

from app import routes


