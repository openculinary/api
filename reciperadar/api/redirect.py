from flask import abort, jsonify, redirect, request

from reciperadar import app
from reciperadar.models.recipes import Recipe
from reciperadar.workers.events import store_event


@app.route("/redirect/recipe/<recipe_id>", methods=["GET", "POST"])
def recipe_redirect(recipe_id):
    recipe = Recipe().get_by_id(recipe_id)
    if not recipe:
        return abort(404)

    store_event.delay(
        event_table="redirects",
        event_data={
            "recipe_id": recipe.id,
            "domain": recipe.domain,
            "dst": recipe.dst,
        },
    )

    if request.method == "GET":
        return redirect(recipe.dst, code=301)
    else:
        return jsonify({})
