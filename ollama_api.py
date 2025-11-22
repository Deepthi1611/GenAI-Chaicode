from fastapi import FastAPI
from ollama import Client
from fastapi import Body

app = FastAPI()
client = Client(
    host="http://localhost:11434"
)

client.pull(model="gemma3:1b")

@app.post("/chat")
def chat(message: str = Body(..., description="The message to send to the chat model")):
    response = client.chat(
        model="gemma3:1b",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message}
        ]
    )
    return {"response": response['message']['content']}
    # return {"response": response}