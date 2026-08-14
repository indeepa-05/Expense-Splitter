"""Basic integration tests for the Jinja web interface and static assets."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_returns_html() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_root_contains_expense_splitter_title() -> None:
    response = client.get("/")

    assert "<title>Expense Splitter</title>" in response.text
    assert "<h1>Expense Splitter</h1>" in response.text


def test_root_contains_key_interface_controls() -> None:
    response = client.get("/")

    assert 'id="people-section"' in response.text
    assert 'id="expense-form"' in response.text
    assert 'value="equal"' in response.text
    assert 'value="percentage"' in response.text
    assert 'id="equal-select-all"' in response.text
    assert 'id="percentage-select-all"' in response.text
    assert 'id="percentage-remaining"' in response.text
    assert 'id="new-session"' in response.text
    assert "Start New Session" in response.text
    assert "Select All" in response.text
    assert "Remaining: 100.00%" in response.text
    assert 'id="balances-section"' in response.text
    assert 'id="settlements-section"' in response.text


def test_static_css_is_served() -> None:
    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert ".page-grid" in response.text


def test_static_js_is_served() -> None:
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert "refreshAll" in response.text
    assert "syncSelectAllState" in response.text
    assert "updatePercentageSummary" in response.text
    assert "normalizeMoneyInput" in response.text
    assert "removePerson" in response.text
    assert "startNewSession" in response.text
