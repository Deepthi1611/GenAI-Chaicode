from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv('GOOGLE_API_KEY'),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

system_prompt = """
You are Elon Musk. You are direct, use memes, love rockets and free speech.
You sometimes reply in all caps for emphasis.
Never break character.
"""

response = client.chat.completions.create(
    model="gemini-2.5-flash",
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Should I learn Python in 2025?"}
    ]
)

print("Input: Should I learn Python in 2025?")
print("Elon Musk says:", response.choices[0].message.content)