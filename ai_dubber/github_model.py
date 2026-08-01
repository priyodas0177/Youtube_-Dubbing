import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

token = os.getenv("GITHUB_TOKEN")

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=token
)

print("Sending request...")

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "Translate this into Bangla: Hello, how are you?"
            }
        ],
        temperature=0
    )

    print("SUCCESS")
    print(response.choices[0].message.content)

except Exception as e:
    print("ERROR")
    print(type(e).__name__)
    print(e)