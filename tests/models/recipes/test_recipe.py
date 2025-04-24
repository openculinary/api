from reciperadar.models.recipes import Recipe


def test_recipe_from_doc(raw_recipe_hit):
    recipe = Recipe().from_doc(raw_recipe_hit["_source"])
    assert recipe.author == "example"
    assert recipe.is_vegetarian

    # assert recipe.directions[0].appliances[0].appliance == "oven"
    # assert recipe.directions[0].utensils[0].utensil == "skewer"

    assert recipe.ingredients[0].product.singular == "one"
    expected_contents = ["one", "content-of-one", "ancestor-of-one"]
    actual_contents = recipe.ingredients[0].product.contents

    assert all([content in actual_contents for content in expected_contents])

    assert recipe.nutrition.carbohydrates == 0
    assert recipe.nutrition.fibre == 0.65

    assert "nutrition" not in recipe.ingredients[0].to_dict()
    assert "is_vegetarian" in recipe.to_dict()

    assert recipe.nutrition.to_dict() == {
        "carbohydrates": {"magnitude": 0, "units": "g"},
        "energy": {"magnitude": 0, "units": "cal"},
        "fat": {"magnitude": 0.01, "units": "g"},
        "fibre": {"magnitude": 0.65, "units": "g"},
        "protein": {"magnitude": 0.05, "units": "g"},
    }

    assert not recipe.is_gluten_free
    assert not recipe.is_vegan
    assert recipe.is_vegetarian


def test_nutrition_source(raw_recipe_hit):
    recipe = Recipe().from_doc(raw_recipe_hit["_source"])
    doc = recipe.to_dict()

    assert recipe.nutrition is not None
    assert "nutrition" in doc
    assert doc["nutrition"] is None
