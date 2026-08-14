"""Helper utilities for endpoint tests.

``client`` / ``app`` fixtures live in ``tests/conftest.py``.
"""


def assert_json_error(resp, status_code: int):
    """Assert that a response is a JSON error with the given status code.

    Returns the parsed JSON body on success.
    """
    assert resp.status_code == status_code, (
        f"expected {status_code}, got {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert isinstance(body, dict)
    return body
