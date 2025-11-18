from dotenv import load_dotenv
import os
from google import genai
from google.genai import types

load_dotenv()  # Loads variables from .env into environment

client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

response = client.models.generate_content(
    model='gemini-2.5-flash-lite', contents='Why is the sky blue?'
)
print(response.text)