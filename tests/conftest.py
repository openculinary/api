import pytest


@pytest.fixture
def raw_recipe_hit():
    return {
        "_index": "recipes",
        "_type": "recipe",
        "_id": "random-id",
        "_score": 10.04635,
        "_source": {
            "title": "Test Recipe",
            "ingredients": [
                {
                    "description": "1 unit of test ingredient one",
                    "product": {"product": "one"}
                },
                {
                    "description": "two units of test ingredient two",
                    "product": {"product": "two"}
                }
            ],
            "image": "http://www.example.com/path/image.png",
            "time": 30,
            "src": "http://www.example.com/recipes/test",
            "domain": "example.com",
            "servings": 2
        },
        "inner_hits": {"ingredients": {"hits": {"hits": []}}}
    }
