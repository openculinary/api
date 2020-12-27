from base58 import b58encode
from flask import abort, jsonify, request
from urllib.request import urlopen
from uuid import uuid4

from reciperadar import app
from reciperadar.models.feedback import Feedback


@app.route('/feedback', methods=['POST'])
def feedback():
    issue, image_data_uri = request.json
    if not image_data_uri.startswith('data:image/png;base64'):
        abort(400)
    image = urlopen(image_data_uri)

    feedback_id = b58encode(uuid4().bytes).decode('utf-8')
    feedback = Feedback(
        id=feedback_id,
        issue=issue,
        image=image.file.read()
    )
    feedback.distribute()

    return jsonify({})
