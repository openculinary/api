from flask import jsonify, request

from reciperadar import app
from reciperadar.models.recipes import RecipeIngredient


@app.route('/api/ingredients')
def ingredients():
    prefix = request.args.get('pre')
    results = RecipeIngredient().autosuggest(prefix)
    return jsonify(results)
