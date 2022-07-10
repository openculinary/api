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
            "id": "example_id",
            "title": "Test Recipe",
            "directions": [
                {
                    "index": 0,
                    "description": "place each skewer in the oven",
                    "markup": (
                        "<mark class='action'>place</mark> each "
                        "<mark class='equipment utensil'>skewer</mark> in the "
                        "<mark class='equipment appliance'>oven</mark>"
                    ),
                }
            ],
            "ingredients": [
                {
                    "index": 0,
                    "description": "1 unit of test ingredient one",
                    "product": {
                        "singular": "one",
                        "plural": "ones",
                        "contents": [
                            "one",
                            "content-of-one",
                            "ancestor-of-one",
                        ],
                    },
                    "product_is_plural": False,
                    "product_name": "one",
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
                },
                {
                    "index": 1,
                    "description": "two units of test ingredient two",
                    "product": {"singular": "two"},
                    "product_is_plural": False,
                    "product_name": "two",
                },
            ],
            "author": "example",
            "image_src": "http://www.example.com/path/image.png?v=123",
            "time": 30,
            "src": "http://www.example.com/recipes/test",
            "dst": "https://www.example.com/recipes/test",
            "domain": "example.com",
            "servings": 2,
            "rating": 4.5,
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
