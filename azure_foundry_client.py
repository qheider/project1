"""Azure Foundry Client for calling Azure OpenAI deployment endpoints."""

import os
import requests


class AzureFoundryClient:
    """A small client to call Azure Foundry / Azure OpenAI deployment endpoints.

    It builds the deployments endpoint if provided a base URL and handles requests and basic parsing.
    """

    def __init__(self, endpoint: str = None, api_key: str = None, deployment: str = None, api_version: str = None):
        self.endpoint = endpoint or os.environ.get("AZURE_FOUNDRY_MODEL_ENDPOINT")
        self.api_key = api_key or os.environ.get("AZURE_FOUNDRY_MODEL_API_KEY")
        self.deployment = deployment or os.environ.get("AZURE_FOUNDRY_MODEL_DEPLOYMENT")
        self.api_version = api_version or os.environ.get("AZURE_FOUNDRY_MODEL_API_VERSION", "2025-01-01-preview")

    def build_endpoint(self) -> str:
        if not self.endpoint:
            raise ValueError("AZURE_FOUNDRY_MODEL_ENDPOINT is not set")
        if "/deployments/" in self.endpoint:
            return self.endpoint
        if not self.deployment:
            raise ValueError("AZURE_FOUNDRY_MODEL_DEPLOYMENT is required when endpoint is a base URL")
        return self.endpoint.rstrip('/') + f"/openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"

    def call(self, prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> str:
        if not (self.endpoint and self.api_key):
            raise ValueError("Azure endpoint or API key not configured")

        endpoint = self.build_endpoint()
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        if not resp.ok:
            body = resp.text or ""
            snippet = body[:500].replace('\n', ' ')
            raise RuntimeError(f"Azure Foundry request failed (status={resp.status_code}): {snippet}")

        try:
            data = resp.json()
        except Exception as e:
            raise RuntimeError("Azure Foundry returned non-JSON response") from e

        try:
            return data.get("choices", [])[0].get("message", {}).get("content", "")
        except Exception:
            raise RuntimeError("Azure Foundry response did not contain assistant content")
