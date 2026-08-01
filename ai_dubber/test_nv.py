import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
    timeout=120,
    max_retries=0
)

print("sending request...")

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role":"user",
            "content":"Translate this into Bangla: Hello world"
        }
    ],
    temperature=0,
    max_tokens=100
)

print(response.choices[0].message.content)