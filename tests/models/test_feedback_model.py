from unittest.mock import MagicMock, call, patch

from reciperadar.models.feedback import Feedback, RemovalRequest
from reciperadar.models.recipes import Recipe


@patch.object(Feedback, "_construct")
def test_feedback(construct):
    construct.return_value = message = MagicMock()
    recipe = Recipe(
        id="test_recipe_id",
        title="marvellous recipe",
        domain="example.test",
        dst="http://example.test",
    )
    report = RemovalRequest(
        recipe_id=recipe.id,
        report_type="removal_request",
        result_index=0,
        content_owner_email="webmaster@example.test",
    )
    Feedback.register_report(recipe, report)

    expected_msg = "Please inspect test_recipe_id for removal_request"
    expected_html = f"<html><body>{expected_msg}</body></html>"

    assert construct.call_args == call(
        subject="Content report: removal_request: test_recipe_id",
        sender="contact@reciperadar.com",
        recipients=["content-reports@reciperadar.com"],
        html=expected_html,
    )
    assert message.send.called
