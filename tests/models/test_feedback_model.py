from unittest.mock import MagicMock, call, patch

from reciperadar.models.feedback import Feedback, RemovalRequest


@patch.object(Feedback, "_construct")
def test_feedback(construct):
    construct.return_value = message = MagicMock()
    report = RemovalRequest(
        recipe_id="test_recipe_id",
        report_type="removal_request",
        result_index=0,
    )
    Feedback.register_report(report)

    expected_msg = "Please inspect test_recipe_id for removal_request"
    expected_html = f"<html><body>{expected_msg}</body></html>"

    assert construct.call_args == call(
        subject="Content report: removal_request: test_recipe_id",
        sender="contact@reciperadar.com",
        recipients=["content-reports@reciperadar.com"],
        html=expected_html,
    )
    assert message.send.called
