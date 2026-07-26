from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

response = client.chat.completions.create(
    model="qwen/qwen3-next-80b-a3b-instruct",
    messages=[
        {
            "role": "user",
            "content": "Translate Hello into Bengali"
        }
    ]
)

print(response.choices[0].message.content)