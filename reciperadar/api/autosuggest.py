from flask import jsonify, request

from reciperadar import app
from reciperadar.search.equipment import EquipmentSearch
from reciperadar.search.ingredients import IngredientSearch


@app.route('/autosuggest/equipment')
def equipment():
    prefix = request.args.get('pre')
    results = EquipmentSearch().autosuggest(prefix)
    return jsonify(results)


@app.route('/autosuggest/ingredients')
def ingredients():
    prefix = request.args.get('pre')
    results = IngredientSearch().autosuggest(prefix)
    return jsonify(results)
