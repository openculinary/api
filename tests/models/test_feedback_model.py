from unittest.mock import MagicMock, call, patch

from reciperadar.models.feedback import Feedback


@patch.object(Feedback, "_construct")
def test_feedback(construct):
    construct.return_value = message = MagicMock()
    Feedback.report("test_recipe_id", "removal_request", 0, {})

    expected_msg = "Please inspect test_recipe_id for removal_request"
    expected_html = f"<html><body>{expected_msg}</body></html>"

    assert construct.call_args == call(
        subject="Content report: removal_request: test_recipe_id",
        sender="contact@reciperadar.com",
        recipients=["content-reports@reciperadar.com"],
        html=expected_html,
    )
    assert message.send.called
