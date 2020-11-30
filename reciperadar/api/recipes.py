from flask import abort, jsonify, request
from user_agents import parse as ua_parser

from reciperadar import app
from reciperadar.models.recipes import Recipe
from reciperadar.search.base import EntityClause
from reciperadar.search.recipes import RecipeSearch
from reciperadar.workers.events import store_event
from reciperadar.workers.searches import recrawl_search


@app.route('/recipes/<recipe_id>/view')
def recipe_view(recipe_id):
    recipe = Recipe().get_by_id(recipe_id)
    if not recipe:
        return abort(404)

    results = {
        'total': 1,
        'results': [recipe.to_dict()],
    }
    return jsonify(results)


def dietary_args(args):
    return [f'is_{arg.replace("-", "_")}' for arg in args if arg in {
        'dairy-free',
        'gluten-free',
        'vegan',
        'vegetarian',
    }]


@app.route('/recipes/search')
def recipe_search():
    include = EntityClause.from_args(request.args.getlist('include[]'))
    exclude = EntityClause.from_args(request.args.getlist('exclude[]'))
    equipment = EntityClause.from_args(request.args.getlist('equipment[]'))
    offset = min(request.args.get('offset', type=int, default=0), (25*10)-10)
    limit = min(request.args.get('limit', type=int, default=10), 10)
    sort = request.args.get('sort', type=str)
    domains = EntityClause.from_args(request.args.getlist('domains[]'))
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

    user_agent = request.headers.get('user-agent')
    suspected_bot = ua_parser(user_agent or '').is_bot

    # Perform a recrawl for the search to find any new/missing recipes
    equipment = EntityClause.term_list(equipment)
    include = EntityClause.term_list(ingredients, lambda x: x.positive)
    exclude = EntityClause.term_list(ingredients, lambda x: not x.positive)
    recrawl_search.delay(include, exclude, equipment, offset)

    # Log a search event
    store_event.delay(
        event_table='searches',
        event_data={
            'suspected_bot': suspected_bot,
            'include': include,
            'exclude': exclude,
            'equipment': equipment,
            'offset': offset,
            'limit': limit,
            'sort': sort,
            'results_ids': [result['id'] for result in results['results']],
            'results_total': results['total']
        }
    )

    return jsonify(results)


@app.route('/recipes/explore')
def recipe_explore():
    ingredients = EntityClause.from_args(request.args.getlist('ingredients[]'))
    dietary_properties = EntityClause.from_args(dietary_args(request.args))

    results = RecipeSearch().explore(
        ingredients=ingredients,
        dietary_properties=dietary_properties,
    )

    return jsonify(results)
