from flask import Flask, render_template, url_for, request, jsonify
import os
import requests
from dotenv import load_dotenv

app = Flask(__name__)

# Load .env file if present so local OPENAI_API_KEY is available during development
load_dotenv()


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


PROFILE = {
    "name": "Quazi Heider",
    "title": "Software Engineer",
    "bio": "Passionate developer with experience in web and backend systems.",
    "email": "qheider@gmail.com",
    "location": "Toronto, Canada",
    "skills": ["Python", "Flask", "Java", "LLM"]
}


@app.route("/")
def index():
    return render_template("profile.html", profile=PROFILE)


def call_Azure_openai_api(prompt: str) -> str:
    """Minimal wrapper to call OpenAI's completions endpoint.

    This uses the environment variable OPENAI_API_KEY. If not present,
    returns a helpful message (so tests can run without network/API key).
    """
    # Prefer Azure Foundry variables if present
    azure_endpoint = os.environ.get("AZURE_FOUNDRY_MODEL_ENDPOINT")
    azure_key = os.environ.get("AZURE_FOUNDRY_MODEL_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if not any([azure_endpoint and azure_key, openai_key]):
        return "No AI API key configured. Set OPENAI_API_KEY or AZURE_FOUNDRY_MODEL_API_KEY in environment to get an AI response."

    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.7,
    }

    # If Azure Foundry details are present, call via the object-oriented client
    if azure_endpoint and azure_key:
        try:
            client = AzureFoundryClient(endpoint=azure_endpoint, api_key=azure_key)
            return client.call(prompt)
        except Exception as e:
            return f"Failed to fetch response from Azure Foundry model: {str(e)}"

    # Fallback to OpenAI (public API) if OPENAI_API_KEY is present
    if openai_key:
        headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json={"model": "gpt-3.5-turbo", **payload},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("choices", [])[0].get("message", {}).get("content", "")
        except Exception:
            return "Failed to fetch response from OpenAI."

    return "No AI API key configured. Set OPENAI_API_KEY or AZURE_FOUNDRY_MODEL_API_KEY in environment to get an AI response."


@app.route('/ask', methods=['GET', 'POST'])
def ask():
    answer = None
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        if question:
            answer = call_Azure_openai_api(question)
        else:
            answer = 'Please enter a question.'

    return render_template('ask.html', answer=answer)


if __name__ == "__main__":
    app.run(debug=True)
