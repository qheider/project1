import os
from openai import AzureOpenAI
## load dotenv if needed
from dotenv import load_dotenv


endpoint = "https://qheid-mgueq40v-eastus2.cognitiveservices.azure.com/"
model_name = "gpt-4.1-nano"
deployment = "gpt-4.1-nano"

subscription_key = os.environ.get("AZURE_FOUNDRY_MODEL_API_KEY")
api_version = "2024-12-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        },
        {
            "role": "user",
            "content": "I am going to dhaka, bangladesh, what should I see?",
        }
    ],
    max_completion_tokens=13107,
    temperature=1.0,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    model=deployment
)

print(response.choices[0].message.content)