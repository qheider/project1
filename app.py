from flask import Flask, render_template, url_for, request, jsonify
from dotenv import load_dotenv
from call_Azure_endpoints import call_Azure_openai_api
from azure_search_client import call_Rag_api
from resume_rag_ollama_oop import ResumeRAG


app = Flask(__name__)

# Load .env file if present so local OPENAI_API_KEY is available during development
load_dotenv()

# Initialize Ollama RAG system
ollama_rag = None

def get_ollama_rag():
    """Lazy initialization of Ollama RAG system."""
    global ollama_rag
    if ollama_rag is None:
        ollama_rag = ResumeRAG(
            pdf_path="C:/resume/resume.pdf",
            chat_model="gpt-oss:20b",
            embedding_model="nomic-embed-text"
        )
        ollama_rag.load_and_process_document()
        ollama_rag.setup_qa_chain()
    return ollama_rag


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


@app.route('/resume-ai', methods=['GET', 'POST'])
def resume_ai():
    answer = None
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        if question:
            answer = call_Rag_api(question)
        else:
            answer = 'Please enter a question.'

    return render_template('resumeAi.html', answer=answer)


@app.route('/resume-ai-ollama', methods=['GET', 'POST'])
def resume_ai_ollama():
    answer = None
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        if question:
            try:
                rag = get_ollama_rag()
                answer = rag.query(question)
            except Exception as e:
                answer = f'Error: {str(e)}'
        else:
            answer = 'Please enter a question.'

    return render_template('resumeAi-Ollama.html', answer=answer)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
