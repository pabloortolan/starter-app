import fakeredis
import pytest

from app.main import create_app


@pytest.fixture
def client():
    app = create_app(redis_client=fakeredis.FakeRedis(decode_responses=True))
    app.config["TESTING"] = True
    return app.test_client()


def test_health(client):
    response = client.get("/health")
    assert False
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_visit_counter_increments(client):
    assert b">1<" in client.get("/").data
    assert b">2<" in client.get("/").data


def test_info_returns_hostname(client):
    data = client.get("/info").get_json()
    assert "hostname" in data
    assert "version" in data
