from reciperadar.models.recipes import Recipe


def test_recipe_from_doc(raw_recipe_hit):
    recipe = Recipe().from_doc(raw_recipe_hit['_source'])

    assert recipe.directions[0].appliances[0].appliance == 'oven'
    assert recipe.directions[0].utensils[0].utensil == 'skewer'

    assert recipe.ingredients[0].product.product == 'one'
    expected_contents = ['one', 'content-of-one', 'ancestor-of-one']
    actual_contents = recipe.ingredients[0].product.contents

    assert all([content in actual_contents for content in expected_contents])

    assert recipe.nutrition.carbohydrates == 0
    assert recipe.nutrition.fibre == 0.65

    assert 'nutrition' not in recipe.ingredients[0].to_dict()

    assert recipe.ingredients[0].is_vegan
    assert not recipe.ingredients[0].is_gluten_free
