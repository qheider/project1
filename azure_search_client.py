import os
from pathlib import Path
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential, AzureCliCredential
from openai import AzureOpenAI
import json

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# --- Configuration ---
# Set these environment variables or replace the placeholders
SERVICE_ENDPOINT = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT", "PUT-YOUR-SEARCH-SERVICE-ENDPOINT-HERE")
INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX_NAME", "PUT-YOUR-INDEX-NAME-HERE")

# Strip quotes if present and validate HTTPS
if SERVICE_ENDPOINT:
    SERVICE_ENDPOINT = SERVICE_ENDPOINT.strip('"\'')
    if not SERVICE_ENDPOINT.startswith('https://'):
        if SERVICE_ENDPOINT.startswith('http://'):
            # Convert http to https
            SERVICE_ENDPOINT = SERVICE_ENDPOINT.replace('http://', 'https://', 1)
            print(f"Warning: Converted endpoint to HTTPS: {SERVICE_ENDPOINT}")
        elif not SERVICE_ENDPOINT.startswith('PUT-YOUR'):
            # Add https:// if missing
            SERVICE_ENDPOINT = 'https://' + SERVICE_ENDPOINT
            print(f"Warning: Added https:// to endpoint: {SERVICE_ENDPOINT}")

if INDEX_NAME:
    INDEX_NAME = INDEX_NAME.strip('"\'')

print(f"Debug - SERVICE_ENDPOINT: {SERVICE_ENDPOINT}")
print(f"Debug - INDEX_NAME: {INDEX_NAME}")

# --- Authentication ---
# Check for API Key first (fastest and most reliable)
API_KEY = os.environ.get("AZURE_SEARCH_API_KEY", "")
if API_KEY and not API_KEY.startswith('PUT-YOUR'):
    API_KEY = API_KEY.strip('"\'')
    print("Attempting authentication with API Key...")
    credential = AzureKeyCredential(API_KEY)
    search_client = SearchClient(
        endpoint=SERVICE_ENDPOINT,
        index_name=INDEX_NAME,
        credential=credential
    )
    print("✓ Successfully authenticated with API Key")
else:
    # Try AzureCliCredential
    try:
        print("Attempting authentication with Azure CLI credentials...")
        credential = AzureCliCredential()
        search_client = SearchClient(
            endpoint=SERVICE_ENDPOINT,
            index_name=INDEX_NAME,
            credential=credential
        )
        print("✓ Successfully authenticated with Azure CLI")
    except Exception as cli_error:
        print(f"Azure CLI authentication failed: {cli_error}")
        try:
            # Fallback to DefaultAzureCredential
            print("Attempting authentication with DefaultAzureCredential...")
            credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)
            search_client = SearchClient(
                endpoint=SERVICE_ENDPOINT,
                index_name=INDEX_NAME,
                credential=credential
            )
            print("✓ Successfully authenticated with DefaultAzureCredential")
        except Exception as default_error:
            print(f"DefaultAzureCredential authentication failed: {default_error}")
            raise Exception("All authentication methods failed. Please configure Azure CLI, DefaultAzureCredential, or provide an API key.")

print("Successfully connected to Azure AI Search.")




# --- LLM Configuration (for your 5 nano model deployment) ---
AOAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "PUT-YOUR-AOAI-ENDPOINT-HERE")
AOAI_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "PUT-YOUR-AOAI-KEY-HERE")
MODEL_DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1-nano")

# Strip quotes and validate HTTPS for OpenAI endpoint
if AOAI_ENDPOINT:
    AOAI_ENDPOINT = AOAI_ENDPOINT.strip('"\'')
    if not AOAI_ENDPOINT.startswith('https://') and not AOAI_ENDPOINT.startswith('PUT-YOUR'):
        if AOAI_ENDPOINT.startswith('http://'):
            AOAI_ENDPOINT = AOAI_ENDPOINT.replace('http://', 'https://', 1)
        else:
            AOAI_ENDPOINT = 'https://' + AOAI_ENDPOINT

if AOAI_KEY:
    AOAI_KEY = AOAI_KEY.strip('"\'')

aoai_client = AzureOpenAI(
    azure_endpoint=AOAI_ENDPOINT,
    api_key=AOAI_KEY,
    api_version="2024-02-15-preview" # Use a version that supports RAG capabilities
)

def search_and_generate_answer(query: str):
    # 1. RETRIEVE: Search Azure AI Search for relevant documents/chunks
    print(f"Searching AI Search for query: '{query}'...")
    
    # Perform a search without specifying fields to get all available fields
    search_results = search_client.search(
        search_text=query,
        top=3 # Get the top 3 most relevant results
    )

    # 2. AUGMENT: Compile the search results into a context string
    context_chunks = []
    citations = []
    
    for i, result in enumerate(search_results):
        # Print first result to see available fields
        if i == 0:
            print(f"\nAvailable fields in result: {list(result.keys())}")
        
        # Try to extract content from various possible field names
        chunk_content = result.get('content') or result.get('chunk') or result.get('text') or str(result)
        source_name = result.get('source_file') or result.get('metadata_storage_name') or result.get('title') or f"Source {i+1}"
        
        context_chunks.append(f"Source [{i+1}]: {chunk_content}")
        citations.append(f"[{i+1}] {source_name}")
    
    context = "\n\n".join(context_chunks)
    
    # 3. GENERATE: Construct the grounded prompt for the LLM

    # This is the crucial instruction (System Prompt) that forces the grounding
    system_prompt = (
        "You are an AI assistant who answers questions based **ONLY** on the "
        "provided context snippets. If the answer cannot be found in the context, "
        "state clearly that the information is not available in the provided sources. "
        "Cite your sources using the format [Source N] at the end of the sentence "
        "where N is the number preceding the source content."
    )
    
    user_prompt = f"Context: {context}\n\nQuestion: {query}"
    
    print("\nSending grounded prompt to LLM...")
    
    response = aoai_client.chat.completions.create(
        model=MODEL_DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0 # Low temperature is better for factual RAG
    )
    
    # Extract the LLM's answer
    llm_answer = response.choices[0].message.content
    
    return {
        "answer": llm_answer,
        "citations": citations
    }

# --- Example Usage ---
user_query = "Give me the list of all experiences mentioned in the documents."
rag_response = search_and_generate_answer(user_query)

print("\n--- LLM Final Answer ---")
print(rag_response['answer'])
print("\n--- Sources Used ---")
print("\n".join(rag_response['citations']))

 

