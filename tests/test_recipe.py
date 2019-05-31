import pytest

from reciperadar.recipe import Recipe


@pytest.fixture
def raw_recipe_hit():
    return {
        "_index": "recipes",
        "_type": "recipe",
        "_id": "random-id",
        "_score": 10.04635,
        "_source": {
            "name": "Test Recipe",
            "ingredients": [
                "1 unit of test ingredient one",
                "two units of test ingredient two"
            ],
            "image": None,
            "time": 30,
            "url": "http://www.example.com/recipes/test"
        }
    }


def test_recipe_from_doc(raw_recipe_hit):
    recipe = Recipe().from_doc(raw_recipe_hit)
    expected_keys = set(['name', 'ingredients', 'time', 'image', 'url'])

    assert expected_keys.issubset(recipe.keys())
