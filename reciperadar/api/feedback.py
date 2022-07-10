from basest.core import encode
from flask import abort, jsonify, request
from urllib.request import urlopen
from uuid import uuid4

from reciperadar import app
from reciperadar.models.feedback import Feedback

ID_SYMBOL_TABLE = [
    s for s in "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
]


@app.route("/feedback", methods=["POST"])
def feedback():
    issue, image_data_uri = request.json
    if not image_data_uri.startswith("data:image/png;base64"):
        abort(400)
    image = urlopen(image_data_uri)

    feedback_id = str().join(
        encode(
            input_data=uuid4().bytes,
            input_base=256,
            input_symbol_table=[b for b in range(256)],
            output_base=58,
            output_symbol_table=ID_SYMBOL_TABLE,
            output_padding="",
            input_ratio=16,
            output_ratio=22,
        )
    )
    feedback = Feedback(id=feedback_id, issue=issue, image=image.file.read())
    feedback.distribute()

    return jsonify({})
