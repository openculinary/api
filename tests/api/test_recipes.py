from unittest.mock import patch

from reciperadar.search.recipes import RecipeSearch
from reciperadar.search.base import EntityClause


@patch.object(RecipeSearch, "query")
def test_search_invalid_sort(query, client):
    response = client.get(
        path="/recipes/search",
        query_string={"sort": "invalid"},
    )

    assert response.status_code == 400
    assert not query.called


@patch("reciperadar.api.recipes.recrawl_search.delay")
@patch("reciperadar.api.recipes.store_event")
@patch("reciperadar.search.recipes.load_ingredient_synonyms")
@patch("reciperadar.search.base.QueryRepository.es.search")
def test_search_empty_query(search, synonyms, store, recrawl, client, raw_recipe_hit):
    hits = [raw_recipe_hit]
    total = len(hits)
    search.return_value = {
        "hits": {"hits": hits, "total": {"value": total}},
        "aggregations": {
            "prefilter": {
                "doc_count": 0,
                "domains": {"buckets": []},
            }
        },
    }
    synonyms.return_value = {}

    response = client.get("/recipes/search")

    assert response.status_code == 200
    assert "refinements" in response.json
    assert "empty_query" in response.json["refinements"]
    assert "domains" in response.json["facets"]


@patch("reciperadar.api.recipes.recrawl_search.delay")
@patch("reciperadar.api.recipes.store_event")
@patch("reciperadar.search.recipes.load_ingredient_synonyms")
@patch("reciperadar.search.recipes.RecipeSearch.query")
def test_search_simple_query(query, synonyms, store, recrawl, client, raw_recipe_hit):
    query.return_value = {
        "authority": "api",
        "total": 0,
        "results": [],
        "facets": {"domains": []},
        "refinements": [],
    }
    synonyms.return_value = {}

    response = client.get("/recipes/search?ingredients[]=tomato&ingredients[]=-tomato")

    assert response.status_code == 200
    assert "refinements" in response.json
    assert "domains" in response.json["facets"]

    expected_clauses = [
        EntityClause(term="tomato", positive=True),
        EntityClause(term="tomato", positive=False),
    ]
    assert query.call_args[1]["ingredients"] == expected_clauses


@patch("werkzeug.datastructures.Headers.get")
@patch("reciperadar.api.recipes.recrawl_search.delay")
@patch("reciperadar.api.recipes.store_event")
@patch.object(RecipeSearch, "query")
def test_search_user_agent_optional(query, store, recrawl, get, client):
    query.return_value = {"results": [], "total": 0}
    get.return_value = None

    response = client.get("/recipes/search", headers={"user-agent": None})

    assert response.status_code == 200


@patch("reciperadar.api.recipes.recrawl_search.delay")
@patch("reciperadar.api.recipes.store_event")
@patch.object(RecipeSearch, "query")
def test_search_recrawling(query, store, recrawl, client):
    query.return_value = {"results": [], "total": 0}

    response = client.get("/recipes/search", headers={"user-agent": None})

    assert response.status_code == 200
    assert recrawl.called is True


@patch("reciperadar.api.recipes.recrawl_search.delay")
@patch("reciperadar.api.recipes.store_event.delay")
@patch.object(RecipeSearch, "query")
def test_bot_search(query, store, recrawl, client):
    query.return_value = {"results": [], "total": 0}

    user_agent = (
        "Mozilla/5.0+",
        "(compatible; UptimeRobot/2.0; http://www.uptimerobot.com/)",
    )
    client.get("/recipes/search", headers={"user-agent": user_agent})

    assert store.called
    assert store.call_args[1]["event_data"]["suspected_bot"] is True
