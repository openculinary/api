from flask import abort, jsonify, request
from user_agents import parse as ua_parser

from reciperadar import app
from reciperadar.models.recipes import Recipe
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


def partition_query_terms(terms):
    partitions = {'include': [], 'exclude': []}
    for term in terms:
        term_length = len(term)
        term = term.lstrip('-')
        partition = 'include' if len(term) == term_length else 'exclude'
        partitions[partition].append(term)
    return partitions


@app.route('/recipes/search')
def recipe_search():
    include = request.args.getlist('include[]')
    exclude = request.args.getlist('exclude[]')
    equipment = request.args.getlist('equipment[]')
    offset = min(request.args.get('offset', type=int, default=0), (25*10)-10)
    limit = min(request.args.get('limit', type=int, default=10), 10)
    sort = request.args.get('sort', type=str)
    domains = request.args.getlist('domains[]')

    if sort and sort not in RecipeSearch.sort_methods():
        return abort(400)

    domains = partition_query_terms(domains)

    results = RecipeSearch().query(
        include=include,
        exclude=exclude,
        equipment=equipment,
        offset=offset,
        limit=limit,
        sort=sort,
        domains=domains
    )

    user_agent = request.headers.get('user-agent')
    suspected_bot = ua_parser(user_agent or '').is_bot

    # Perform a recrawl for the search to find any new/missing recipes
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
