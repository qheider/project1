import os

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

endpoint = "https://qheid-mgueq40v-eastus2.openai.azure.com/openai/v1/"
deployment_name = "gpt-4.1-nano"
api_key = os.getenv("AZURE_FOUNDRY_MODEL_API_KEY")
client = OpenAI(
    base_url=endpoint,
    api_key=api_key
)

completion = client.chat.completions.create(
    model=deployment_name,
    messages=[
        {
            "role": "user",
            "content": "What is the capital of France?",
        }
    ],
    temperature=0.7,
)

print(completion.choices[0].message)