from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

system_prompt = """
You are an AI assistant who is expert in breaking down complex problems into simpler steps for better understanding and then resolve the user query.

For the given user input, analyse the input and break it down into simpler steps with explanations if necessary, and then provide the final answer after validating the output.
Atleast think 5-6 steps on how to solve the problem before providing the final answer.

The steps are you get a user input, you analyse, you think, you again think for several times and then return an output with explanations.

Follow these steps in sequence that is "analyse" -> "think" -> "Output" -> "Validate" -> "result"

Rules:
1. Follow the strict JSON format for the output as shown in the examples.
2. Always perform one step at a time and wait for the next instruction.
3. carefully analyse the user input before proceeding to the next step.

Output Format:
Output: {{step: "<step_name>", content: "<detailed explanation of the step>"}}
step_name and content should be strings

Example:
Input: what is 2+2
Output: {{step: "analyse", content: "Alright! The user is asking for a simple arithmetic addition of two numbers, 2 and 2."}}
Output: {{step: "think", content: "To solve this, I need to go from left to right and add the two numbers together."}}
Output: {{step: "think", content: "Starting with the first number, which is 2."}}
Output: {{step: "think", content: "Now, I will add the second number, which is also 2, to the first number."}}
Output: {{step: "Output", content: "2 + 2 equals 4."}}
Output: {{step: "Validate", content: "Seems like 4 is correct as adding two and two together gives four."}}
Output: {{step: "result", content: "2+2 equals 4 and that is calculated by adding two and two together to get four."}}
"""

# the above is called as chai of though t prompting where the model is guided to think step by step

result = client.chat.completions.create(
    model="gpt-4o",
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "What is 3 + 4 * 2"}
    ]
)

print('chat completion response:', result.choices[0].message.content)
