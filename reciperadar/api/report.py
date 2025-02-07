from flask import abort, jsonify, request

from reciperadar import app
from reciperadar.models.recipes import Recipe
from reciperadar.models.feedback import Feedback


@app.route("/recipes/<recipe_id>/report", methods=["POST"])
def recipe_report(recipe_id):
    recipe = Recipe().get_by_id(recipe_id)
    if not recipe:
        return abort(404)

    report_json = request.json
    report_type = report_json["report_type"]
    result_index = report_json["result_index"]
    report_data = report_json[report_type]

    Feedback.report(
        report_type=report_type,
        result_index=result_index,
        report_data=report_data,
    )

    return jsonify({"recipe_id": recipe_id})
