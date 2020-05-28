import os

from flask import Flask
from flask_cors import CORS
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix


app = Flask(__name__)
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
    SQLALCHEMY_DATABASE_URI='sqlite://',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)
app.url_map.strict_slashes = False
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
CORS(app, origins=[
    r'^https://\w+.reciperadar.com$',
    r'^http://localhost$',
    r'^http://192.168.\d+.\d+$',
])
mail = Mail(app)
db = SQLAlchemy(app)


import reciperadar.api.feedback
import reciperadar.api.recipes
import reciperadar.api.redirect
import reciperadar.api.search
