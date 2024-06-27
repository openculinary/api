from flask import abort, jsonify, request

from reciperadar import app
from reciperadar.search.equipment import EquipmentSearch
from reciperadar.search.ingredients import IngredientSearch


@app.route("/autosuggest/equipment")
def equipment():
    prefix = request.args.get("pre") or ""
    if not (3 <= len(prefix) <= 64):
        return abort(400)
    results = EquipmentSearch().autosuggest(prefix)
    return jsonify(results)


@app.route("/autosuggest/ingredients")
def ingredients():
    prefix = request.args.get("pre") or ""
    if not (3 <= len(prefix) <= 64):
        return abort(400)
    results = IngredientSearch().autosuggest(prefix)
    return jsonify(results)
