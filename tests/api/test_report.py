from unittest.mock import patch

from reciperadar.api.report import Feedback
from reciperadar.models.recipes.recipe import Recipe


@patch.object(Feedback, "report")
@patch.object(Recipe, "get_by_id")
def test_unsafe_content_report(get_recipe_by_id, report, client):
    recipe = Recipe(id="example_id", domain="example.test", dst="http://example.test")
    get_recipe_by_id.return_value = recipe

    report_data = {
        "report_type": "unsafe_content",
        "result_index": 0,
        "unsafe_content": {"content_type": "other"},
    }
    response = client.post(
        path="/recipes/recipe_id_0/report",
        json=report_data,
    )

    assert report.called
    assert response.status_code == 200
