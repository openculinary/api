from flask import Flask, jsonify
from flask_mail import Mail
from flask_jsonschema import JsonSchema, ValidationError
import os


app = Flask(__name__)
app.config.update(
    JSONSCHEMA_DIR=os.path.join(app.root_path, 'api/schemas'),
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
)
jsonschema = JsonSchema(app)
mail = Mail(app)


@app.errorhandler(ValidationError)
def on_validation_error(e):
    return jsonify({'error': e.message}), 400


import reciperadar.api.emails
import reciperadar.api.recipes
import reciperadar.api.reminders
import reciperadar.api.search