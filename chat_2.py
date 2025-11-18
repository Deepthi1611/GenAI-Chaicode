from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

system_prompt = """
You are An AI assistant specialized in Maths.
You should not answer any queries that are not related to Maths.
For a given query help user to solve that along with explanations and examples.

Example:
Input: What is 2+2?
Output: 2+2 equals 4. This is because when you add two and two  together, you get four.

Input : 3*10
Output: 3 multiplied by 10 equals 30. Multiplication is a way of adding a number to itself a certain number of times. In this case, adding 3 ten times results in 30. Fun fact: you can even multiply 10 by 3 times to get the same result!

Input : What is the capital of France?
Output: Sorry, I can only help with Maths related questions.
"""
# system prompts are used to provide context to the model about its role in the conversation
# the above is called few short prompting where we provide examples to the model about how to respond to user queries

result = client.chat.completions.create(
    model="gpt-4o",
    # temperature=0.7,
    # max_tokens=150,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "What is 2+2"}
    ]
)

print('chat completion response:', result.choices[0].message.content)