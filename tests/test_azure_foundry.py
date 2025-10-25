import os
import json
import pytest
import requests
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()


@pytest.mark.skipif(os.environ.get('RUN_AZURE_TEST') != '1', reason='Run Azure Foundry tests only when RUN_AZURE_TEST=1')
def test_azure_foundry_direct_call():
    """Directly call the Azure Foundry chat/completions endpoint.

    Environment variables required (set in .env or environment):
      - AZURE_FOUNDRY_MODEL_ENDPOINT  (either full deployments URL or base resource URL)
      - AZURE_FOUNDRY_MODEL_API_KEY
    Optional:
      - AZURE_FOUNDRY_MODEL_DEPLOYMENT (if endpoint is base URL)
      - AZURE_FOUNDRY_MODEL_API_VERSION (defaults to 2025-01-01-preview)
    """

    endpoint = os.environ.get('AZURE_FOUNDRY_MODEL_ENDPOINT')
    api_key = os.environ.get('AZURE_FOUNDRY_MODEL_API_KEY')
    deployment = os.environ.get('AZURE_FOUNDRY_MODEL_DEPLOYMENT')
    api_version = os.environ.get('AZURE_FOUNDRY_MODEL_API_VERSION', '2025-01-01-preview')

    assert endpoint, 'AZURE_FOUNDRY_MODEL_ENDPOINT is required to run this test'
    assert api_key, 'AZURE_FOUNDRY_MODEL_API_KEY is required to run this test'

    if '/deployments/' not in endpoint:
        assert deployment, 'AZURE_FOUNDRY_MODEL_DEPLOYMENT is required when endpoint is a base URL'
        endpoint = endpoint.rstrip('/') + f"/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

    headers = {'api-key': api_key, 'Content-Type': 'application/json'}
    payload = {
        'messages': [{'role': 'user', 'content': 'Hello from pytest integration test'}],
        'max_tokens': 50,
        'temperature': 0.2,
    }

    resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)

    # If non-2xx, include body for debugging
    try:
        resp.raise_for_status()
    except Exception:
        body = resp.text[:500].replace('\n', ' ')
        pytest.fail(f'Azure Foundry call failed (status={resp.status_code}): {body}')

    data = resp.json()
    print('Full response:', json.dumps(data, indent=2))
    # Basic assertions on response shape
    assert 'choices' in data and isinstance(data['choices'], list)
    first = data['choices'][0]
    print('Response choice:', json.dumps(first, indent=2))
    assert 'message' in first and 'content' in first['message']
    assert isinstance(first['message']['content'], str) and len(first['message']['content']) > 0
