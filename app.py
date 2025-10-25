from flask import Flask, render_template, url_for, request, jsonify
import os
import requests
from dotenv import load_dotenv

app = Flask(__name__)

# Load .env file if present so local OPENAI_API_KEY is available during development
load_dotenv()

PROFILE = {
    "name": "Alex Doe",
    "title": "Software Engineer",
    "bio": "Passionate developer with experience in web and backend systems.",
    "email": "alex.doe@example.com",
    "location": "San Francisco, CA",
    "skills": ["Python", "Flask", "Docker", "Postgres"]
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

    # If Azure Foundry details are present, call that endpoint
    if azure_endpoint and azure_key:
        azure_deployment = os.environ.get("AZURE_FOUNDRY_MODEL_DEPLOYMENT")
        azure_api_version = os.environ.get("AZURE_FOUNDRY_MODEL_API_VERSION", "2025-01-01-preview")

        endpoint = azure_endpoint
        if "/deployments/" not in azure_endpoint:
            if not azure_deployment:
                return "AZURE_FOUNDRY_MODEL_ENDPOINT looks like a base URL; please set AZURE_FOUNDRY_MODEL_DEPLOYMENT to build the full endpoint."
            endpoint = azure_endpoint.rstrip('/') + f"/openai/deployments/{azure_deployment}/chat/completions?api-version={azure_api_version}"

        headers = {"api-key": azure_key, "Content-Type": "application/json"}
        azure_payload = payload.copy()
        try:
            resp = requests.post(endpoint, headers=headers, json=azure_payload, timeout=30)
        except Exception as e:
            return f"Failed to reach Azure Foundry endpoint: {str(e)}"

        # If non-2xx, return an informative message with a snippet of the body
        if not resp.ok:
            body = resp.text or ""
            snippet = body[:500].replace('\n', ' ')
            return f"Azure Foundry request failed (status={resp.status_code}): {snippet}"

        try:
            data = resp.json()
        except Exception:
            return "Azure Foundry returned non-JSON response"

        # Extract assistant message
        try:
            return data.get("choices", [])[0].get("message", {}).get("content", "")
        except Exception:
            return "Azure Foundry response did not contain assistant content"

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
