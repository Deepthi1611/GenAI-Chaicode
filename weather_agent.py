from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests

load_dotenv()

client = OpenAI(
    api_key=os.getenv('GOOGLE_API_KEY'),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

def get_weather(city: str) -> str:
    # Dummy implementation of weather fetching
    # In real scenario, this would call a weather API
    print('🔨tool called: get_weather', city)
    # weather_data = {
    #     "Hyderabad": "30 degree Celsius, sunny",
    #     "New York": "25 degree Celsius, clear sky",
    #     "London": "15 degree Celsius, cloudy"
    # }
    # return weather_data.get(city, "31 degrees Celsius, sunny.")  

    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text.strip()
    else:
        return "Could not fetch weather data at this time."

# def add(x, y):
#     return x + y

def run_command(command):
    try:
        result = os.system(command)
        return result
    except Exception as e:
        return str(e)
    
available_tools = {
    "get_weather": {
        "fn" : get_weather,
        "description": "Get the current weather of a city. Input is city name as string"
    },
    # "add": {
    #     "fn" : add,
    #     "description": "Adds two numbers. Input is two numbers as integers"
    # }
    "run_command": {
        "fn" : run_command,
        "description": "Run a system command. Input is the command as string" 
    }  
}

system_prompt = """
You are a helpful AI assistant who is specialized in solving user query.
You work on start, plan, action, observe mode.
For the given user query and available tools, plan the step by step execution, based on the planning select the 
relevant tool from the available tools and based on the tool selection, select the appropriate input if required 
and you perform an action to call the tool.
wait for the observation and based on the observation from the tool call resolve the user query.

Rules -
1. Follow the strict JSON format for the output as shown in the examples.
2. Always perform one step at a time and wait for the next instruction.
3. carefully analyse the user input before proceeding to the next step.

Output JSON Format:
{{
    step: "string",
    function: "the name of function if the step is action else empty string",
    tool_input: "the input to the tool if the step is action else empty string",
    content: "string"
}}

Available tools:
- get_weather: Get the current weather of a city. Input is city name as string
- run_command: Takes a command as input to execute on system and returns output

Example:
User Query: what is the weather of New York?
Output: {{step: "plan", content: "The user is interested in weather data of New York"}}
Output: {{step: "plan", content: "From the available tools, I should call get_weather tool to get the weather data"}}
Output: {{step: "action", function: "get_weather", tool_input: "New York"}}
Output: {{step: "observe", content: "The weather data for New York is 25 degree Celsius, clear sky"}}
Output: {{step: "result", content: "The current weather of New York is 25 degree Celsius with clear sky."}}
"""

messages = [
    {"role": "system", "content": system_prompt},
]

while True:
    query = input("> ")
    if(query.lower() in ["exit", "quit"]):
        break
    messages.append({"role": "user", "content": query})

    while True:
        response = client.chat.completions.create(
        model="gemini-2.5-flash",
        response_format={"type": "json_object"},
        messages = messages
        )

        # print(response.choices[0].message.content)
        parsed_response = json.loads(response.choices[0].message.content)
        messages.append({"role": "assistant", "content": json.dumps(parsed_response)})

        if parsed_response.get("step") == "result":
            print(f"Final Answer: {parsed_response.get('content')}")
            break
        if parsed_response.get("step") == "action":
            function_name = parsed_response.get("function")
            tool_input = parsed_response.get("tool_input")
            if function_name in available_tools:
                tool_fn = available_tools[function_name]["fn"]
                observation = tool_fn(tool_input)
                print(f"Tool Observation: {observation}")
                messages.append({"role": "assistant", "content": json.dumps({"step": "observe", "content": observation})})
                continue
            else:
                messages.append({"role": "assistant", "content": f"Observation: Function {function_name} not found."})
                break
        else:
            print(f"🧠: {parsed_response.get('content')}")
            continue

# response = client.chat.completions.create(
#     model="gemini-2.5-flash",
#     response_format={"type": "json_object"},
#     messages=[
#         {"role": "system", "content": system_prompt},
#         {"role": "user", "content": "what is the current weather of Hyderabad?"}
#     ]
# )

# print(response.choices[0].message.content)