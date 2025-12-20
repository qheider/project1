# Project Setup and Troubleshooting Guide

## Overview
This document provides comprehensive setup instructions, architecture details, and troubleshooting steps for the Flask application with Azure AI Search integration.

## Table of Contents
1. [Project Structure](#project-structure)
2. [Environment Setup](#environment-setup)
3. [Azure Configuration](#azure-configuration)
4. [Authentication Setup](#authentication-setup)
5. [Common Issues and Solutions](#common-issues-and-solutions)
6. [Code Refactoring History](#code-refactoring-history)

---

## Project Structure

```
project1/
├── app.py                          # Main Flask application
├── azure_foundry_client.py         # Azure Foundry/OpenAI client class
├── azure_search_client.py          # Azure AI Search client with RAG
├── call_Azure_endpoints.py         # Azure/OpenAI API wrapper
├── .env                            # Environment variables (DO NOT COMMIT)
├── .gitignore                      # Git ignore file
├── requirements.txt                # Python dependencies
├── static/
│   └── styles.css                  # CSS styling
├── templates/
│   ├── profile.html                # Profile page template
│   ├── ask.html                    # AI question page template
│   └── app_azure_openai.py         # Azure OpenAI example script
├── scripts/
│   ├── check_azure_foundry.py
│   └── run_test_azure_foundry.py
└── tests/
    ├── test_app.py
    ├── test_azure_foundry.py
    └── test1.py
```

---

## Environment Setup

### 1. Create Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

**Key Dependencies:**
- Flask>=2.0
- pytest
- requests
- python-dotenv
- openai
- azure-search-documents
- azure-identity

### 3. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Azure Foundry / Azure OpenAI Configuration
AZURE_FOUNDRY_MODEL_ENDPOINT="https://your-endpoint.cognitiveservices.azure.com/"
AZURE_FOUNDRY_MODEL_DEPLOYMENT="gpt-4.1-nano"
AZURE_FOUNDRY_MODEL_API_VERSION=2025-01-01-preview
AZURE_FOUNDRY_MODEL_API_KEY="your-api-key-here"

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT="https://your-endpoint.cognitiveservices.azure.com/openai/deployments/gpt-4.1-nano/chat/completions?api-version=2024-05-01-preview"
AZURE_OPENAI_API_KEY="your-api-key-here"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4.1-nano"

# Azure AI Search Configuration
AZURE_SEARCH_SERVICE_ENDPOINT="https://your-search-service.search.windows.net"
AZURE_SEARCH_INDEX_NAME="your-index-name"
AZURE_SEARCH_API_KEY="your-search-api-key"

# Azure Project Configuration
AZURE_SUBSCRIPTION_ID="your-subscription-id"
AZURE_LOCATION="eastus2"
```

**⚠️ Important:** Add `.env` to `.gitignore` to prevent committing secrets.

---

## Azure Configuration

### Azure AI Search Setup

#### Option 1: Using API Key (Recommended for Development)

1. Get the API key from Azure Portal or CLI:
```powershell
az search admin-key show --resource-group <resource-group> --service-name <search-service> --query primaryKey -o tsv
```

2. Add to `.env`:
```bash
AZURE_SEARCH_API_KEY="your-api-key"
```

#### Option 2: Using RBAC (Role-Based Access Control)

1. Assign required roles:
```powershell
# Search Index Data Reader (for read access)
az role assignment create \
  --role "Search Index Data Reader" \
  --assignee <your-email@domain.com> \
  --scope "/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.Search/searchServices/<search-service>"

# Search Service Contributor (for full access)
az role assignment create \
  --role "Search Service Contributor" \
  --assignee <your-email@domain.com> \
  --scope "/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.Search/searchServices/<search-service>"
```

2. Login to Azure CLI:
```powershell
az login
```

3. Verify authentication:
```powershell
az account get-access-token --resource https://search.azure.com
```

**Note:** RBAC permissions can take 5-10 minutes to propagate.

---

## Authentication Setup

The application supports multiple authentication methods in priority order:

### 1. API Key Authentication (Highest Priority)
- Most reliable for development
- No propagation delay
- Uses `AzureKeyCredential`

### 2. Azure CLI Credential
- Uses your Azure CLI login
- Good for local development
- Requires `az login`

### 3. DefaultAzureCredential (Fallback)
- Tries multiple authentication methods
- Best for production with Managed Identity
- Supports environment variables, managed identity, Azure CLI, etc.

### Code Implementation

```python
from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

# Authentication fallback chain in AzureSearchRAGClient
class AzureSearchRAGClient:
    def _create_search_client(self) -> SearchClient:
        # Try API Key first (fastest and most reliable)
        if self.search_api_key and not self.search_api_key.startswith('PUT-YOUR'):
            credential = AzureKeyCredential(self.search_api_key)
            return SearchClient(
                endpoint=self.search_endpoint,
                index_name=self.search_index,
                credential=credential
            )
        
        # Fallback to Azure CLI
        try:
            credential = AzureCliCredential()
            return SearchClient(
                endpoint=self.search_endpoint,
                index_name=self.search_index,
                credential=credential
            )
        except Exception:
            # Last resort: DefaultAzureCredential
            credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)
            return SearchClient(
                endpoint=self.search_endpoint,
                index_name=self.search_index,
                credential=credential
            )
```

---

## Common Issues and Solutions

### Issue 1: "Operation returned an invalid status 'Forbidden'"

**Cause:** Insufficient permissions to access Azure Search index.

**Solutions:**

1. **Use API Key** (Fastest Solution):
   ```powershell
   az search admin-key show --resource-group <rg> --service-name <service> --query primaryKey -o tsv
   ```
   Add to `.env` as `AZURE_SEARCH_API_KEY`

2. **Assign RBAC Roles**:
   ```powershell
   az role assignment create --role "Search Index Data Reader" --assignee <email> --scope <scope>
   ```
   Wait 5-10 minutes for propagation

3. **Refresh Azure CLI Credentials**:
   ```powershell
   az account clear
   az login
   ```

---

### Issue 2: "Bearer token authentication is not permitted for non-TLS protected (non-https) URLs"

**Cause:** Endpoint URL is not using HTTPS or is malformed.

**Solutions:**

1. **Check `.env` file** - Ensure endpoint starts with `https://`:
   ```bash
   AZURE_SEARCH_SERVICE_ENDPOINT="https://your-service.search.windows.net"
   ```

2. **Remove Quotes** - Code automatically strips quotes:
   ```python
   SERVICE_ENDPOINT = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT", "").strip('"\'')
   ```

3. **Validate HTTPS** - Code automatically converts http to https:
   ```python
   if not SERVICE_ENDPOINT.startswith('https://'):
       SERVICE_ENDPOINT = SERVICE_ENDPOINT.replace('http://', 'https://', 1)
   ```

---

### Issue 3: "Invalid expression: Could not find a property named 'content'"

**Cause:** Field names in the search query don't match the actual index schema.

**Solution:**

1. **Discover Available Fields**:
   ```python
   search_results = search_client.search(search_text=query, top=1)
   for result in search_results:
       print(f"Available fields: {list(result.keys())}")
       break
   ```

2. **Use Actual Field Names**:
   ```python
   # AzureSearchRAGClient automatically handles multiple field names
   chunk_content = (
       result.get('content') or 
       result.get('chunk') or 
       result.get('text') or 
       str(result)
   )
   source_name = (
       result.get('source_file') or 
       result.get('metadata_storage_name') or 
       result.get('title') or 
       f"Source {i+1}"
   )
   ```

3. **Don't Specify Fields** (Get All):
   ```python
   search_results = search_client.search(search_text=query, top=3)
   # Don't use select=['content', 'source_file']
   ```

---

### Issue 4: Environment Variables Not Loading

**Cause:** `.env` file not being loaded by `python-dotenv`.

**Solution:**

1. **Install python-dotenv**:
   ```powershell
   pip install python-dotenv
   ```

2. **Load Environment Variables**:
   ```python
   from pathlib import Path
   from dotenv import load_dotenv
   
   env_path = Path(__file__).parent / '.env'
   load_dotenv(dotenv_path=env_path)
   ```

3. **Verify Loading**:
   ```python
   import os
   print(f"Endpoint: {os.getenv('AZURE_SEARCH_SERVICE_ENDPOINT')}")
   ```

---

### Issue 5: Flask App Won't Start

**Cause:** Port already in use or missing dependencies.

**Solutions:**

1. **Check if port 5000 is in use**:
   ```powershell
   netstat -ano | findstr :5000
   ```

2. **Kill process on port 5000**:
   ```powershell
   taskkill /PID <process-id> /F
   ```

3. **Use different port**:
   ```python
   if __name__ == "__main__":
       app.run(debug=True, port=5001)
   ```

---

## Code Refactoring History

### 1. Extracted `AzureFoundryClient` Class

**Before:**
- All Azure Foundry logic in `app.py`

**After:**
- Created `azure_foundry_client.py` with OOP structure
- Imported in `app.py`: `from azure_foundry_client import AzureFoundryClient`

**Benefits:**
- Better separation of concerns
- Reusable across multiple files
- Easier to test

---

### 2. Created `call_Azure_endpoints.py`

**Purpose:** Unified wrapper for Azure Foundry and OpenAI APIs

**Key Classes:**
- `AzureOpenAIWrapper` - Main wrapper class with OOP design
- `call_Azure_openai_api()` - Backward-compatible function

**Features:**
- Automatic fallback (Azure → OpenAI)
- Configuration validation
- Error handling

**Usage:**
```python
from call_Azure_endpoints import call_Azure_openai_api

response = call_Azure_openai_api("What is the capital of France?")
```

---

### 3. Refactored `azure_search_client.py` to OOP

**Improvements:**
- Full OOP structure with `AzureSearchRAGClient` class
- Multi-method authentication (API Key → Azure CLI → DefaultAzureCredential)
- Automatic HTTPS validation and endpoint correction
- Environment variable loading with `python-dotenv`
- RAG (Retrieval-Augmented Generation) implementation
- Clean, minimal design with only essential methods

**Key Methods:**
- `search()` - Search Azure AI Search index for relevant documents
- `generate_answer()` - Generate grounded AI responses using RAG pattern

**Architecture:**
1. **RETRIEVE**: Search for relevant documents using Azure AI Search
2. **AUGMENT**: Build context from search results with proper field mapping
3. **GENERATE**: Create AI response grounded in retrieved context with citations

**Usage:**
```python
from azure_search_client import AzureSearchRAGClient

# Initialize client (uses .env variables by default)
client = AzureSearchRAGClient()

# Simple search
results = client.search(query="software engineer experience", top=3)

# RAG: Get AI-generated answer with citations
response = client.generate_answer(query="What experiences are mentioned?")
print(response['answer'])
print("\n".join(response['citations']))
```

**Constructor Parameters** (all optional, defaults to .env):
```python
client = AzureSearchRAGClient(
    search_endpoint="https://your-service.search.windows.net",
    search_index="your-index-name",
    search_api_key="your-search-key",
    openai_endpoint="https://your-endpoint.cognitiveservices.azure.com/",
    openai_api_key="your-openai-key",
    openai_deployment="gpt-4.1-nano"
)
```

---

### 4. Created `app_azure_openai.py`

**Purpose:** Standalone example using OpenAI SDK with Azure

**Key Features:**
- Uses `openai` library directly
- OOP with `AzureOpenAIClient` class
- Supports chat completions
- Convenience methods: `ask()` and `chat_completion()`

---

## Running the Application

### Development Mode

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run Flask app
python app.py
```

Access at: http://127.0.0.1:5000

### Debug Mode

The app runs with `debug=True` by default:
- Auto-reload on file changes
- Detailed error messages
- Debugger PIN displayed in console

---

## Testing

### Run All Tests

```powershell
pytest
```

### Run Specific Test File

```powershell
pytest tests/test_app.py
```

### Run Azure Search Client

```powershell
python azure_search_client.py
```

**Expected Output:**
```
--- LLM Final Answer ---
Based on the provided sources, here are the experiences mentioned:

[Detailed AI-generated answer with citations like [Source 1], [Source 2], etc.]

--- Sources Used ---
[1] Resume.pdf
[2] Experience_Document.docx
[3] CV.pdf
```

**What Happens:**
1. `AzureSearchRAGClient` initializes with .env configuration
2. Loads environment variables using python-dotenv
3. Authenticates via API Key (or falls back to Azure CLI/DefaultAzureCredential)
4. Validates HTTPS endpoints
5. Executes search query against Azure AI Search
6. Retrieves top 3 relevant document chunks
7. Sends context + query to Azure OpenAI (gpt-4.1-nano)
8. Returns grounded answer with source citations

---

## Architecture Overview

### Flask Application (`app.py`)
- Routes: `/` (profile), `/ask` (AI questions)
- Uses `call_Azure_endpoints.py` for AI responses
- Renders Jinja2 templates

### Azure Foundry Client (`azure_foundry_client.py`)
- Handles Azure OpenAI deployments
- Builds endpoint URLs
- Manages authentication with API keys

### Azure Search Client (`azure_search_client.py`)
- **OOP Class**: `AzureSearchRAGClient`
- **RAG Pattern**: Retrieval-Augmented Generation implementation
- Searches Azure AI Search index for relevant documents
- Generates AI responses grounded in search results with source citations
- Multi-method authentication with automatic fallback
- HTTPS validation and endpoint correction

**Key Features:**
- `search()` method for document retrieval
- `generate_answer()` method for RAG-based responses
- Automatic field mapping (handles 'chunk', 'content', 'text', 'title', etc.)
- Temperature=0.0 for factual responses
- Grounding system prompt to prevent hallucination

### API Wrapper (`call_Azure_endpoints.py`)
- Unified interface for Azure Foundry and OpenAI
- Automatic fallback logic
- Error handling and retry logic

---

## Security Best Practices

1. **Never commit `.env` file** - Always in `.gitignore`
2. **Use environment variables** - No hardcoded secrets
3. **Prefer RBAC over API keys** - In production
4. **Rotate API keys regularly** - Update in Azure Portal
5. **Use HTTPS only** - Code enforces this
6. **Limit API key permissions** - Use read-only keys when possible

---

## Useful Commands

### Azure CLI

```powershell
# Login
az login

# List subscriptions
az account list --output table

# Set subscription
az account set --subscription <subscription-id>

# Get access token
az account get-access-token --resource https://search.azure.com

# List role assignments
az role assignment list --assignee <email> --output table

# Get search service details
az search service show --name <service> --resource-group <rg>

# Get API key
az search admin-key show --name <service> --resource-group <rg>
```

### Git Commands

```powershell
# Check current branch
git branch

# Create new branch
git checkout -b feature/new-feature

# Stage changes
git add .

# Commit
git commit -m "Description of changes"

# Push to remote
git push origin <branch-name>
```

---

## Troubleshooting Checklist

- [ ] Virtual environment activated?
- [ ] All dependencies installed?
- [ ] `.env` file exists and properly formatted?
- [ ] Azure CLI logged in (`az login`)?
- [ ] RBAC roles assigned (if not using API key)?
- [ ] Endpoint URLs use HTTPS?
- [ ] API keys valid and not expired?
- [ ] Port 5000 available (for Flask)?
- [ ] Search index exists and has documents?
- [ ] Field names match index schema?

---

## Additional Resources

- [Azure AI Search Documentation](https://learn.microsoft.com/en-us/azure/search/)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Python-dotenv Documentation](https://github.com/theskumar/python-dotenv)
- [Azure Identity SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme)

---

## Version History

- **v1.0** - Initial Flask application
- **v1.1** - Added Azure Foundry integration
- **v1.2** - Refactored to OOP structure
- **v1.3** - Added Azure AI Search with RAG
- **v1.4** - Fixed authentication and HTTPS issues
- **v1.5** - Improved error handling and field mapping
- **v1.6** - Converted azure_search_client.py to full OOP with AzureSearchRAGClient class

---

## Contact & Support

For issues or questions:
- Repository: https://github.com/qheider/project1
- Branch: Azure-AI_search_connection
- Current Date: December 19, 2025

---

*Last Updated: December 19, 2025*
