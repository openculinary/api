from flask import abort, jsonify, redirect, request

from reciperadar import app
from reciperadar.models.recipes import Recipe
from reciperadar.utils.bots import is_suspected_bot
from reciperadar.workers.events import store_event


@app.route("/redirect/recipe/<recipe_id>", methods=["GET", "POST"])
def recipe_redirect(recipe_id):
    recipe = Recipe().get_by_id(recipe_id)
    if not recipe:
        return abort(404)

    user_agent = request.headers.get("user-agent")
    suspected_bot = request.method == "GET" or is_suspected_bot(user_agent)

    store_event.delay(
        event_table="redirects",
        event_data={
            "suspected_bot": suspected_bot,
            "recipe_id": recipe.id,
            "domain": recipe.domain,
            "dst": recipe.dst,
        },
    )

    if request.method == "GET":
        return redirect(recipe.dst, code=301)
    else:
        return jsonify({})
