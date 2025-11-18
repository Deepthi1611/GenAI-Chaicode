from openai import OpenAI
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

try:
    models = client.models.list()
    print("API key works!")
except Exception as e:
    print(e)
