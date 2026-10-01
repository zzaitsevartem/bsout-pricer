import pytest

pytestmark = pytest.mark.integration


async def test_feedback_accepts_valid_message(client):
    resp = await client.post(
        "/api/feedback",
        json={
            "name": "Ivan",
            "email": "ivan@example.com",
            "subject": "Вопрос",
            "message": "Здравствуйте!",
        },
    )

    assert resp.status_code == 202, resp.text
    assert resp.json()["detail"]


async def test_feedback_rejects_invalid_email(client):
    resp = await client.post(
        "/api/feedback",
        json={"name": "Ivan", "email": "not-an-email", "subject": "x", "message": "y"},
    )

    assert resp.status_code == 422


async def test_feedback_rejects_empty_message(client):
    resp = await client.post(
        "/api/feedback",
        json={"name": "Ivan", "email": "ivan@example.com", "subject": "x", "message": ""},
    )

    assert resp.status_code == 422
