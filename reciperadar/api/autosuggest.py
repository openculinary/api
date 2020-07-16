from flask import jsonify, request

from reciperadar import app
from reciperadar.models.recipes import RecipeEquipment
from reciperadar.models.recipes import RecipeIngredient


@app.route('/autosuggest/equipment')
def equipment():
    prefix = request.args.get('pre')
    results = RecipeEquipment().autosuggest(prefix)
    return jsonify(results)


@app.route('/autosuggest/ingredients')
def ingredients():
    prefix = request.args.get('pre')
    results = RecipeIngredient().autosuggest(prefix)
    return jsonify(results)
