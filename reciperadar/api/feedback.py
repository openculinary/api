from flask import abort, jsonify, request
from urllib.request import urlopen

from reciperadar import app
from reciperadar.models.feedback import Feedback


@app.route("/feedback", methods=["POST"])
def feedback():
    issue, image_data_uri = request.json
    if not image_data_uri.startswith("data:image/png;base64"):
        abort(400)
    image = urlopen(image_data_uri)

    Feedback.distribute(issue=issue, image=image.file.read())

    return jsonify({})
