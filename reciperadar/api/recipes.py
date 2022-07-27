from datetime import datetime, timedelta

from flask import abort, jsonify, request
from user_agents import parse as ua_parser

from reciperadar import app
from reciperadar.models.recipes import Recipe
from reciperadar.search.base import EntityClause
from reciperadar.search.ingredients import IngredientSearch
from reciperadar.search.recipes import RecipeSearch
from reciperadar.workers.events import store_event
from reciperadar.workers.searches import recrawl_search


@app.route("/recipes/<recipe_id>/view")
def recipe_view(recipe_id):
    recipe = Recipe().get_by_id(recipe_id)
    if not recipe:
        return abort(404)

    results = {
        "total": 1,
        "results": [recipe.to_dict()],
    }
    return jsonify(results)


def dietary_args(args):
    return [
        f'is_{arg.replace("-", "_")}'
        for arg in args
        if arg
        in {
            "dairy-free",
            "gluten-free",
            "vegan",
            "vegetarian",
        }
    ]


@app.before_first_request
def load_ingredient_synonyms():
    # Return cached synonyms if they are available and have not yet expired
    if hasattr(app, "ingredient_synonyms"):
        if datetime.utcnow() < app.ingredient_synonyms_loaded_at + timedelta(hours=1):
            return app.ingredient_synonyms

    # Attempt to update the synonym cache
    synonyms = IngredientSearch().synonyms()
    if synonyms:
        app.ingredient_synonyms = synonyms
        app.ingredient_synonyms_loaded_at = datetime.utcnow()

    # Return the latest-known synonyms
    if hasattr(app, "ingredient_synonyms"):
        return app.ingredient_synonyms


@app.route("/recipes/search")
def recipe_search():
    include = EntityClause.from_args(request.args.getlist("include[]"))
    exclude = EntityClause.from_args(request.args.getlist("exclude[]"))
    equipment = EntityClause.from_args(request.args.getlist("equipment[]"))
    offset = min(request.args.get("offset", type=int, default=0), (25 * 10) - 10)
    limit = min(request.args.get("limit", type=int, default=10), 10)
    sort = request.args.get("sort", type=str)
    domains = EntityClause.from_args(request.args.getlist("domains[]"))
    dietary_properties = EntityClause.from_args(dietary_args(request.args))

    if sort and sort not in RecipeSearch.sort_methods():
        return abort(400)

    # TODO: Remove: backwards-compatibility
    # Disable the 'positive' flag on excluded ingredients
    for ingredient in exclude:
        ingredient.positive = False

    # TODO: Remove: backwards-compatibility
    # Combine the include and exclude ingredient lists
    ingredients = include + exclude

    results = RecipeSearch().query(
        ingredients=ingredients,
        equipment=equipment,
        offset=offset,
        limit=limit,
        sort=sort,
        domains=domains,
        dietary_properties=dietary_properties,
    )

    user_agent = request.headers.get("user-agent")
    suspected_bot = ua_parser(user_agent or "").is_bot

    # Perform a recrawl for the search to find any new/missing recipes
    synonyms = load_ingredient_synonyms()
    equipment = EntityClause.term_list(equipment)
    include = EntityClause.term_list(ingredients, synonyms, lambda x: x.positive)
    exclude = EntityClause.term_list(ingredients, synonyms, lambda x: not x.positive)
    recrawl_search.delay(include, exclude, equipment, offset)

    # Log a search event
    store_event.delay(
        event_table="searches",
        event_data={
            "suspected_bot": suspected_bot,
            "path": request.path,
            "include": include,
            "exclude": exclude,
            "equipment": equipment,
            "offset": offset,
            "limit": limit,
            "sort": sort,
            "results_ids": [result["id"] for result in results["results"]],
            "results_total": results["total"],
        },
    )

    return jsonify(results)


@app.route("/recipes/explore")
def recipe_explore():
    ingredients = EntityClause.from_args(request.args.getlist("ingredients[]"))
    dietary_properties = EntityClause.from_args(dietary_args(request.args))

    results = RecipeSearch().explore(
        ingredients=ingredients,
        dietary_properties=dietary_properties,
    )

    user_agent = request.headers.get("user-agent")
    suspected_bot = ua_parser(user_agent or "").is_bot

    # TODO: De-duplicate this logic; it also appears in RecipeSearch.explore
    synonyms = load_ingredient_synonyms()
    include = EntityClause.term_list(ingredients, synonyms, lambda x: x.positive)
    exclude = EntityClause.term_list(ingredients, synonyms, lambda x: not x.positive)
    depth = len(ingredients)
    limit = 10 if depth >= 3 else 0

    # Log a search event
    store_event.delay(
        event_table="searches",
        event_data={
            "suspected_bot": suspected_bot,
            "path": request.path,
            "include": include,
            "exclude": exclude,
            "equipment": [],
            "offset": 0,
            "limit": limit,
            "sort": None,
            "results_ids": [result["id"] for result in results["results"]],
            "results_total": results["total"],
        },
    )

    return jsonify(results)
