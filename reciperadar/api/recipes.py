import sys

from flask import abort, jsonify, request

from reciperadar import app
from reciperadar.models.feedback import (
    Correction,
    Feedback,
    ProblemReport,
    RemovalRequest,
    UnsafeContent,
)
from reciperadar.models.recipes import Recipe
from reciperadar.search.base import EntityClause
from reciperadar.search.recipes import RecipeSearch
from reciperadar.utils.bots import is_suspected_bot
from reciperadar.workers.events import store_event
from reciperadar.workers.searches import recrawl_search


@app.route("/recipes/<recipe_id>/view")
def recipe_view(recipe_id):
    recipe = Recipe().get_by_id(recipe_id)
    if not recipe:
        return abort(404)

    if recipe.redirected_id:
        print(
            f"Redirecting from_id={recipe.id} to_id={recipe.redirected_id}",
            file=sys.stderr,
        )
        return recipe_view(recipe.redirected_id)

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


@app.route("/recipes/search")
def recipe_search():
    ingredients = EntityClause.from_args(request.args.getlist("ingredients[]"))
    equipment = EntityClause.from_args(request.args.getlist("equipment[]"))
    offset = min(request.args.get("offset", type=int, default=0), (25 * 10) - 10)
    limit = min(request.args.get("limit", type=int, default=10), 10)
    sort = request.args.get("sort", type=str)
    domains = EntityClause.from_args(request.args.getlist("domains[]"))
    dietary_properties = EntityClause.from_args(dietary_args(request.args))

    if sort and sort not in RecipeSearch.sort_methods():
        return abort(400)

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
    suspected_bot = is_suspected_bot(user_agent)

    include = EntityClause.term_list(ingredients, lambda x: x.positive)
    exclude = EntityClause.term_list(ingredients, lambda x: x.negative)
    dietary_properties = EntityClause.term_list(dietary_properties)

    # Perform a recrawl for the search to find any new/missing recipes
    if not suspected_bot:
        recrawl_search.delay(include, exclude, [], dietary_properties, offset)

    # Log a search event
    store_event.delay(
        event_table="searches",
        event_data={
            "suspected_bot": suspected_bot,
            "path": request.path,
            "include": include,
            "exclude": exclude,
            "equipment": [],
            "dietary_properties": dietary_properties,
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
    suspected_bot = is_suspected_bot(user_agent)

    include = EntityClause.term_list(ingredients, lambda x: x.positive)
    exclude = EntityClause.term_list(ingredients, lambda x: x.negative)
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


@app.route("/recipes/report", methods=["POST"])
def recipe_report():
    try:
        recipe_id = request.form.get("recipe-id")
    except Exception:
        return abort(400)
    if not recipe_id:
        return abort(400)

    recipe = Recipe().get_by_id(recipe_id)
    if not recipe:
        return abort(404)

    try:
        report_type = request.form.get("report-type")
        result_index = 0  # request.form.get("result-index", type=int)
    except Exception:
        return abort(400)

    if not report_type:
        return abort(400)

    if result_index is None:
        return abort(400)

    try:
        report: ProblemReport | None = None
        match report_type:
            case "removal-request":
                content_owner_email, content_reuse_policy, content_noindex_directive = (
                    request.form.get("content-owner-email"),
                    request.form.get("content-reuse-policy"),
                    request.form.get("content-noindex-directive"),
                )
                if not (content_owner_email or content_reuse_policy):
                    return abort(400)
                if content_noindex_directive is None:
                    return abort(400)
                report = RemovalRequest(
                    recipe_id=recipe_id,
                    report_type=report_type,
                    result_index=result_index,
                    content_owner_email=content_owner_email,
                    content_reuse_policy=content_reuse_policy,
                    content_noindex_directive=bool(content_noindex_directive),
                )
            case "unsafe-content":
                report = UnsafeContent(
                    recipe_id=recipe_id,
                    report_type=report_type,
                    result_index=result_index,
                )
            case "correction":
                content_expected, content_found = (
                    request.form.get("content-expected"),
                    request.form.get("content-found"),
                )
                if not (content_expected and content_found):
                    return abort(400)
                if content_expected == content_found:
                    return abort(400)
                report = Correction(
                    recipe_id=recipe_id,
                    report_type=report_type,
                    result_index=result_index,
                    content_expected=content_expected,
                    content_found=content_found,
                )
            case _:
                return abort(400)
    except AssertionError:
        return abort(400)

    Feedback.register_report(recipe, report)
    return jsonify({"recipe_id": report["recipe_id"]})
