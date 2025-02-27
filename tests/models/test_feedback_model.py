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

    subject, sender, recipients, html = (
        construct.call_args.kwargs.get(field)
        for field in ("subject", "sender", "recipients", "html")
    )
    assert subject == "Content report: removal_request: test_recipe_id"
    assert sender == "contact@reciperadar.com"
    assert recipients == ["content-reports@reciperadar.com"]
    assert "recipe removal request" in html
    assert "https://www.reciperadar.com/#action=view&id=test_recipe_id" in html
    assert f'<a href="mailto:webmaster@example.test">' in html
