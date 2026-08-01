from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
    timeout=90
)


texts = [
"So you want to use AI models like GPT and Gemini",
"but don't want to pay for them",
"Today I will show OpenRouter"
]


prompt="""
Translate these English sentences into natural Bangladeshi Bangla.

Return JSON only:

{
"translations":[
"bangla1",
"bangla2",
"bangla3"
]
}

"""


for i,t in enumerate(texts,1):
    prompt += f"\nSEGMENT_{i}: {t}"


print("sending...")


response = client.chat.completions.create(

    model="meta/llama-3.2-3b-instruct",

    response_format={
        "type":"json_object"
    },

    messages=[
        {
            "role":"user",
            "content":prompt
        }
    ],

    temperature=0.2,

    max_tokens=4096
)


print(response.choices[0].message.content)