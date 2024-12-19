import pytest

from reciperadar import app


@pytest.fixture
def client():
    yield app.test_client()


@pytest.fixture
def raw_recipe_hit():
    return {
        "_index": "recipes",
        "_type": "recipe",
        "_id": "random-id",
        "_score": 10.04635,
        "_source": {
            "id": "recipe_id_0",
            "title": "Test Recipe",
            "directions": [
                {
                    "id": "direction_id_0",
                    "index": 0,
                    "description": "place each skewer in the oven",
                    "markup": (
                        "<mark class='action'>place</mark> each "
                        # "<mark class='equipment utensil'>skewer</mark> in the "
                        # "<mark class='equipment appliance'>oven</mark>"
                        "<mark class='utensil'>skewer</mark> in the "
                        "<mark class='appliance'>oven</mark>"
                    ),
                }
            ],
            "ingredients": [
                {
                    "id": "ingredient_id_0",
                    "index": 0,
                    "description": "1 unit of test ingredient one",
                    "product": {
                        "singular": "one",
                        "plural": "ones",
                        "contents": [
                            "ancestor-of-one",
                            "content-of-one",
                            "one",
                        ],
                    },
                    "product_is_plural": False,
                    "product_name": "one",
                    "nutrition": {
                        "id": "nutrition_id_0",
                        "carbohydrates": 0,
                        "carbohydrates_units": "g",
                        "energy": 0,
                        "energy_units": "cal",
                        "fat": 0.01,
                        "fat_units": "g",
                        "fibre": 0.65,
                        "fibre_units": "g",
                        "protein": 0.05,
                        "protein_units": "g",
                    },
                },
                {
                    "id": "ingredient_id_1",
                    "index": 1,
                    "description": "two units of test ingredient two",
                    "product": {"singular": "two"},
                    "product_is_plural": False,
                    "product_name": "two",
                },
            ],
            "author": "example",
            "time": 30,
            "src": "http://www.example.test/recipes/test",
            "dst": "https://www.example.test/recipes/test",
            "domain": "example.test",
            "servings": 2,
            "rating": 4.5,
            "indexed_at": "1970-01-01T01:02:03.456789",
            "nutrition": {
                "carbohydrates": 0,
                "carbohydrates_units": "g",
                "energy": 0,
                "energy_units": "cal",
                "fat": 0.01,
                "fat_units": "g",
                "fibre": 0.65,
                "fibre_units": "g",
                "protein": 0.05,
                "protein_units": "g",
            },
            "is_vegetarian": True,
        },
        "inner_hits": {"ingredients": {"hits": {"hits": []}}},
    }
