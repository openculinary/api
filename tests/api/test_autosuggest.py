import pytest


@pytest.mark.parametrize(
    "prefix",
    [
        None,
        "",
        "a",
        "0",
        "1",
        "test" * 25,
    ],
)
def test_autosuggest_equipment_invalid_prefix(client, prefix):
    url = "/autosuggest/equipment" + (f"?pre={prefix}" if prefix else "")
    response = client.get(url)
    assert response.status_code == 400


@pytest.mark.parametrize(
    "prefix",
    [
        None,
        "",
        "a",
        "0",
        "1",
        "test" * 25,
    ],
)
def test_autosuggest_ingredients_invalid_prefix(client, prefix):
    url = "/autosuggest/ingredients" + (f"?pre={prefix}" if prefix else "")
    response = client.get(url)
    assert response.status_code == 400
