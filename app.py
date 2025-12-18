from flask import Flask, render_template, url_for, request, jsonify
from dotenv import load_dotenv
from call_Azure_endpoints import call_Azure_openai_api

app = Flask(__name__)

# Load .env file if present so local OPENAI_API_KEY is available during development
load_dotenv()


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


@app.route('/ask', methods=['GET', 'POST'])
def ask():
    answer = None
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        if question:
            answer = call_Azure_openai_api(question)
        else:
            answer = 'Please enter a question.'

    return render_template('ask.html', answer=answer) # only render ask.html on GET or after processing POST


if __name__ == "__main__":
    app.run(debug=True)
