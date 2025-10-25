import os
import sys
import pytest

# Ensure the project root is on sys.path so pytest can import app.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client


def test_index_shows_name(client):
    res = client.get('/')
    assert res.status_code == 200
    assert b'Alex Doe' in res.data


def test_ask_get(client):
    res = client.get('/ask')
    assert res.status_code == 200
    assert b'Ask AI' in res.data


def test_ask_post_without_key_returns_helpful_message(client, monkeypatch):
    # Ensure both OPENAI and AZURE keys are not set
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('AZURE_FOUNDRY_MODEL_API_KEY', raising=False)
    monkeypatch.delenv('AZURE_FOUNDRY_MODEL_ENDPOINT', raising=False)
    res = client.post('/ask', data={'question': 'Hello AI'})
    assert res.status_code == 200
    assert b'No AI API key configured' in res.data


def test_ask_post_empty_question_shows_prompt(client):
    res = client.post('/ask', data={'question': ''})
    assert res.status_code == 200
    assert b'Please enter a question.' in res.data
