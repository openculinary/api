from unittest.mock import call, patch

from reciperadar.models.recipes import Recipe


def _expected_redirect_call(recipe, suspected_bot=False):
    return call(
        event_table="redirects",
        event_data={
            "suspected_bot": suspected_bot,
            "recipe_id": recipe.id,
            "domain": recipe.domain,
            "dst": recipe.dst,
        },
    )


@patch("reciperadar.api.recipes.store_event.delay")
@patch.object(Recipe, "get_by_id")
def test_redirect_retrieval(get_recipe_by_id, store_event, client):
    recipe = Recipe(id="example_id", domain="example.test", dst="http://example.test")
    get_recipe_by_id.return_value = recipe

    response = client.get(
        path="/redirect/recipe/example_id",
        headers={"Referer": "http://example.test/origin"},
    )

    assert response.status_code == 301
    assert response.location == recipe.dst
    assert store_event.call_args == _expected_redirect_call(recipe, suspected_bot=True)


@patch("reciperadar.api.recipes.is_suspected_bot")
@patch("reciperadar.api.recipes.store_event.delay")
@patch.object(Recipe, "get_by_id")
def test_redirect_ping(get_recipe_by_id, store_event, is_suspected_bot, client):
    recipe = Recipe(id="example_id", domain="example.test", dst="http://example.test")
    get_recipe_by_id.return_value = recipe
    is_suspected_bot.return_value = False

    response = client.post(
        path="/redirect/recipe/example_id",
        data={
            "Ping-From": "http://example.test/origin",
            "Ping-To": recipe.dst,
        },
    )

    assert response.status_code == 200
    assert store_event.call_args == _expected_redirect_call(recipe)
