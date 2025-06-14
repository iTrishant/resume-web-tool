from dotenv import load_dotenv
import os
from google.ai.generativelanguage_v1beta import GenerativeServiceClient

load_dotenv()

# Client automatically uses GOOGLE_API_KEY from environment
client = GenerativeServiceClient()

# List available models
models = client.list_models()

# Print their names
print([model.name for model in models])
