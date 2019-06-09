from base58 import b58encode
from datetime import datetime
from flask import jsonify, request
from sqlalchemy.exc import IntegrityError
from urllib.parse import unquote
from uuid import uuid4
from validate_email import validate_email

from reciperadar.app import app
from reciperadar.models.email import Email
from reciperadar.services.background.emails import issue_verification_token
from reciperadar.services.database import Database


@app.route('/api/emails/register', methods=['POST'])
def register_email():
    email = request.form.get('email')
    email = unquote(email)

    if not validate_email(email, check_mx=True):
        return jsonify({'error': 'invalid_email'}), 400

    token = b58encode(uuid4().bytes).decode('utf-8')
    record = Email(
        email=email,
        token=token
    )

    session = Database().get_session()
    session.add(record)
    try:
        session.commit()
        issue_verification_token.delay(email, token)
    except IntegrityError:
        pass
    session.close()
    return jsonify({})


@app.route('/api/emails/verify')
def verify_email():
    token = request.args.get('token')

    session = Database().get_session()
    email = session.query(Email).filter(Email.token == token).first()
    if email:
        email.verified_at = datetime.utcnow()
        session.commit()
    session.close()
    return jsonify({'token': token})