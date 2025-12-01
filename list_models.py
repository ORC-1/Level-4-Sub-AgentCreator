import os
from google import genai
from dotenv import load_dotenv

load_dotenv("src/agent_creator/.env") # Load from specific location if needed, or just .env

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("No API key found")
    exit(1)

client = genai.Client(api_key=api_key)

try:
    print("Listing models...")
    # In google-genai, it might be client.models.list()
    for model in client.models.list():
        print(model.name)
except Exception as e:
    print(f"Error listing models: {e}")
