from flask import jsonify, request

from reciperadar import app
from reciperadar.models.recipes import RecipeEquipment


@app.route('/api/equipment')
def equipment():
    prefix = request.args.get('pre')
    results = RecipeEquipment().autosuggest(prefix)
    return jsonify(results)
