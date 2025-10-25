"""Manual script to call the Azure Foundry model. Usage:

    python scripts/run_test_azure_foundry.py "Hello"

Reads env vars from .env (already loaded by app) or the environment.
"""
import os
import sys
from app import call_openai_api

if __name__ == '__main__':
    prompt = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else 'Hello from manual test'
    print('Prompt:', prompt)
    res = call_openai_api(prompt)
    print('Response:\n', res)
