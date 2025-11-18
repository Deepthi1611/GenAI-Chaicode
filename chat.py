from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

result = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "Hello! Can you provide a brief overview of the Eiffel Tower?"} # zero shot prompting
    ]
)

print('chat completion response:', result.choices[0].message.content)

# single shot prompting where we provide only the user query to the model