"""Azure AI Search client with RAG (Retrieval-Augmented Generation) capabilities."""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential, AzureCliCredential
from openai import AzureOpenAI


class AzureSearchRAGClient:
    """Azure AI Search client with RAG capabilities for grounded AI responses."""

    def __init__(
        self,
        search_endpoint: Optional[str] = None,
        search_index: Optional[str] = None,
        search_api_key: Optional[str] = None,
        openai_endpoint: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        openai_deployment: Optional[str] = None
    ):
        """
        Initialize Azure Search RAG Client.
        
        Args:
            search_endpoint: Azure Search service endpoint
            search_index: Search index name
            search_api_key: Search API key (optional, uses Azure CLI if not provided)
            openai_endpoint: Azure OpenAI endpoint
            openai_api_key: Azure OpenAI API key
            openai_deployment: OpenAI deployment/model name
        """
        # Load environment variables
        env_path = Path(__file__).parent / '.env'
        load_dotenv(dotenv_path=env_path)
        
        # Initialize search configuration
        self.search_endpoint = self._validate_endpoint(
            search_endpoint or os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT", "")
        )
        self.search_index = (search_index or os.getenv("AZURE_SEARCH_INDEX_NAME", "")).strip('"\'')
        self.search_api_key = (search_api_key or os.getenv("AZURE_SEARCH_API_KEY", "")).strip('"\'')
        
        # Initialize OpenAI configuration
        self.openai_endpoint = self._validate_endpoint(
            openai_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", "")
        )
        self.openai_api_key = (openai_api_key or os.getenv("AZURE_OPENAI_API_KEY", "")).strip('"\'')
        self.openai_deployment = (openai_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1-nano")).strip('"\'')
        
        # Initialize clients
        self.search_client = self._create_search_client()
        self.openai_client = self._create_openai_client()

    def _validate_endpoint(self, endpoint: str) -> str:
        """Validate and fix endpoint URL to ensure HTTPS."""
        endpoint = endpoint.strip('"\'')
        
        if not endpoint or endpoint.startswith('PUT-YOUR'):
            return endpoint
            
        if not endpoint.startswith('https://'):
            if endpoint.startswith('http://'):
                endpoint = endpoint.replace('http://', 'https://', 1)
            else:
                endpoint = 'https://' + endpoint
        
        return endpoint

    def _create_search_client(self) -> SearchClient:
        """Create and authenticate Azure Search client."""
        if not self.search_endpoint or not self.search_index:
            raise ValueError("Search endpoint and index name are required")
        
        # Try API Key first
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

    def _create_openai_client(self) -> AzureOpenAI:
        """Create Azure OpenAI client."""
        if not self.openai_endpoint or not self.openai_api_key:
            raise ValueError("OpenAI endpoint and API key are required")
        
        return AzureOpenAI(
            azure_endpoint=self.openai_endpoint,
            api_key=self.openai_api_key,
            api_version="2024-02-15-preview"
        )

    def search(self, query: str, top: int = 3) -> List[Dict]:
        """
        Search Azure AI Search index.
        
        Args:
            query: Search query string
            top: Maximum number of results
            
        Returns:
            List of search results
        """
        search_results = self.search_client.search(search_text=query, top=top)
        return [result for result in search_results]

    def generate_answer(self, query: str, top: int = 3) -> Dict[str, any]:
        """
        Generate grounded AI answer using RAG (Retrieval-Augmented Generation).
        
        Args:
            query: User question
            top: Number of search results to use as context
            
        Returns:
            Dictionary with 'answer' and 'citations' keys
        """
        # 1. RETRIEVE: Search for relevant documents
        search_results = self.search(query, top)
        
        # 2. AUGMENT: Build context from search results
        context_chunks = []
        citations = []
        
        for i, result in enumerate(search_results):
            # Extract content from available fields
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
            
            context_chunks.append(f"Source [{i+1}]: {chunk_content}")
            citations.append(f"[{i+1}] {source_name}")
        
        context = "\n\n".join(context_chunks)
        
        # 3. GENERATE: Get AI response grounded in context
        system_prompt = (
            "You are an AI assistant who answers questions based **ONLY** on the "
            "provided context snippets. If the answer cannot be found in the context, "
            "state clearly that the information is not available in the provided sources. "
            "Cite your sources using the format [Source N] at the end of the sentence "
            "where N is the number preceding the source content."
        )
        
        user_prompt = f"Context: {context}\n\nQuestion: {query}"
        
        response = self.openai_client.chat.completions.create(
            model=self.openai_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        
        return {
            "answer": response.choices[0].message.content,
            "citations": citations
        }

def call_Rag_api(prompt: str) -> str:
    """
    Convenience function to maintain backward compatibility.
    
    Args:
        prompt: The prompt to send to the model
        
    Returns:
        The response from the API
    """
    wrapper = AzureSearchRAGClient()
    return wrapper.generate_answer(prompt)



