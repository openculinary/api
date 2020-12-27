from unittest.mock import call, patch

from reciperadar.models.feedback import Feedback


@patch.object(Feedback, 'distribute')
def test_feedback(distribute, client):
    response = client.post(
        path='/feedback',
        json=[
            {},
            'data:image/png;base64,',
        ]
    )

    assert response.status_code == 200
    assert distribute.call_arg


@patch.object(Feedback, 'distribute')
def test_feedback_invalid_uri(distribute, client):
    response = client.post(
        path='/feedback',
        json=[
            {},
            'http://example.org',
        ]
    )

    assert response.status_code == 400
    assert not distribute.called
