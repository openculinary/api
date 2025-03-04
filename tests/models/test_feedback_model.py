from unittest.mock import MagicMock, patch

import pytest

from reciperadar.models.feedback import Correction, Feedback, RemovalRequest
from reciperadar.models.recipes import Recipe


@pytest.fixture
def reported_recipe():
    return Recipe(
        id="test_recipe_id",
        title="marvellous recipe",
        domain="example.test",
        dst="http://example.test",
    )


@patch.object(Feedback, "_construct")
def test_feedback(construct, reported_recipe):
    construct.return_value = MagicMock()
    report = RemovalRequest(
        recipe_id=reported_recipe.id,
        report_type="removal_request",
        result_index=0,
        content_owner_email="webmaster@example.test",
    )
    Feedback.register_report(reported_recipe, report)

    subject, sender, recipients, html = (
        construct.call_args.kwargs.get(field)
        for field in ("subject", "sender", "recipients", "html")
    )
    assert subject == "Content report: removal_request: test_recipe_id"
    assert sender == "contact@reciperadar.com"
    assert recipients == ["content-reports@reciperadar.com"]
    assert "recipe removal request" in html
    assert "https://www.reciperadar.com/#action=view&id=test_recipe_id" in html
    assert '<a href="mailto:webmaster@example.test">' in html


@patch.object(Feedback, "_construct")
def test_feedback_html_escaping(construct, reported_recipe):
    construct.return_value = MagicMock()
    report = Correction(
        recipe_id=reported_recipe.id,
        report_type="correction",
        result_index=0,
        content_expected="<marquee>challenging input</marquee>",
        content_found="<script>unexpected</script>",
    )
    Feedback.register_report(reported_recipe, report)

    subject, sender, recipients, html = (
        construct.call_args.kwargs.get(field)
        for field in ("subject", "sender", "recipients", "html")
    )
    assert subject == "Content report: correction: test_recipe_id"
    assert sender == "contact@reciperadar.com"
    assert recipients == ["content-reports@reciperadar.com"]
    assert "<script>" not in html
    assert "<marquee>" not in html
    assert "&lt;script&gt;" in html
