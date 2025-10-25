"""Standalone script to test Azure Foundry chat/completions endpoint.

Usage:
    python scripts/check_azure_foundry.py "Hello"

Reads these env vars (or from .env):
  - AZURE_FOUNDRY_MODEL_ENDPOINT
  - AZURE_FOUNDRY_MODEL_API_KEY
Optional:
  - AZURE_FOUNDRY_MODEL_DEPLOYMENT (when endpoint is a base URL)
  - AZURE_FOUNDRY_MODEL_API_VERSION

Exits with code 0 on success, non-zero on failure. Prints response JSON.
"""
import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()


def build_endpoint(endpoint, deployment, api_version):
    if '/deployments/' in endpoint:
        return endpoint
    if not deployment:
        raise ValueError('AZURE_FOUNDRY_MODEL_DEPLOYMENT is required when endpoint is a base URL')
    return endpoint.rstrip('/') + f"/openai/deployments/{deployment}/chat/completions?api-version={api_version}"


def call_azure(endpoint, api_key, prompt, deployment=None, api_version='2025-01-01-preview'):
    endpoint = build_endpoint(endpoint, deployment, api_version)
    headers = {'api-key': api_key, 'Content-Type': 'application/json'}
    payload = {
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 150,
        'temperature': 0.7,
    }
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
    try:
        resp.raise_for_status()
    except Exception:
        body = resp.text[:1000].replace('\n', ' ')
        print(f'ERROR: request failed status={resp.status_code} body={body}', file=sys.stderr)
        sys.exit(2)

    data = resp.json()
    print(json.dumps(data, indent=2))
    # extract and print assistant content if present
    try:
        assistant = data['choices'][0]['message']['content']
        print('\n--- Assistant response ---\n')
        print(assistant)
    except Exception:
        print('\nNo assistant content found in response', file=sys.stderr)
    return 0


if __name__ == '__main__':
    prompt = "who are you?"
    endpoint = os.environ.get('AZURE_FOUNDRY_MODEL_ENDPOINT')
    api_key = os.environ.get('AZURE_FOUNDRY_MODEL_API_KEY')
    deployment = os.environ.get('AZURE_FOUNDRY_MODEL_DEPLOYMENT')
    api_version = os.environ.get('AZURE_FOUNDRY_MODEL_API_VERSION', '2025-01-01-preview')

    if not endpoint or not api_key:
        print('Please set AZURE_FOUNDRY_MODEL_ENDPOINT and AZURE_FOUNDRY_MODEL_API_KEY in environment or .env', file=sys.stderr)
        sys.exit(1)

    try:
        call_azure(endpoint, api_key, prompt, deployment, api_version)
    except Exception as e:
        print('Exception:', str(e), file=sys.stderr)
        sys.exit(3)
    