"""Azure and OpenAI API client wrapper."""

import os
import requests
from azure_foundry_client import AzureFoundryClient


class AzureOpenAIWrapper:
    """Wrapper class for calling Azure Foundry and OpenAI APIs."""

    def __init__(self):
        """Initialize the API wrapper with environment variables."""
        self.azure_endpoint = os.environ.get("AZURE_FOUNDRY_MODEL_ENDPOINT")
        self.azure_key = os.environ.get("AZURE_FOUNDRY_MODEL_API_KEY")
        self.openai_key = os.environ.get("OPENAI_API_KEY")

    def is_configured(self) -> bool:
        """Check if any API configuration is available."""
        return bool((self.azure_endpoint and self.azure_key) or self.openai_key)

    def call_azure_foundry(self, prompt: str) -> str:
        """
        Call Azure Foundry API.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            The response from Azure Foundry
            
        Raises:
            Exception: If the API call fails
        """
        client = AzureFoundryClient(endpoint=self.azure_endpoint, api_key=self.azure_key)
        return client.call(prompt)

    def call_openai(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
        """
        Call OpenAI public API.
        
        Args:
            prompt: The prompt to send to the model
            model: The OpenAI model to use
            
        Returns:
            The response from OpenAI
            
        Raises:
            Exception: If the API call fails
        """
        headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 150,
            "temperature": 0.7,
        }

        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [])[0].get("message", {}).get("content", "")

    def call(self, prompt: str) -> str:
        """
        Call the appropriate API based on available configuration.
        Prefers Azure Foundry over OpenAI if both are configured.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            The response from the API or an error message
        """
        if not self.is_configured():
            return "No AI API key configured. Set OPENAI_API_KEY or AZURE_FOUNDRY_MODEL_API_KEY in environment to get an AI response."

        # Prefer Azure Foundry if available
        if self.azure_endpoint and self.azure_key:
            try:
                return self.call_azure_foundry(prompt)
            except Exception as e:
                return f"Failed to fetch response from Azure Foundry model: {str(e)}"

        # Fallback to OpenAI
        if self.openai_key:
            try:
                return self.call_openai(prompt)
            except Exception:
                return "Failed to fetch response from OpenAI."

        return "No AI API key configured. Set OPENAI_API_KEY or AZURE_FOUNDRY_MODEL_API_KEY in environment to get an AI response."


def call_Azure_openai_api(prompt: str) -> str:
    """
    Convenience function to maintain backward compatibility.
    
    Args:
        prompt: The prompt to send to the model
        
    Returns:
        The response from the API
    """
    wrapper = AzureOpenAIWrapper()
    return wrapper.call(prompt)
