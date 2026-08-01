import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("GITHUB_TOKEN")
)

segments = [
    "So you want to use AI models like GPT and Gemini.",
    "In this video, I will introduce OpenRouter.",
    "It allows you to connect multiple AI models."
]


prompt = """
Translate English subtitles into natural spoken Bangladeshi Bangla.

Rules:
1. Return ONLY JSON.
2. Exactly one translation for each segment.
3. Never merge segments.
4. Never split segments.

Format:

{
 "translations":[
   "translation 1",
   "translation 2",
   "translation 3"
 ]
}

Segments:
"""

for i, text in enumerate(segments, 1):
    prompt += f"""
<SEGMENT_{i}>
{text}
</SEGMENT_{i}>
"""


response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "You are a professional subtitle translator."
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    temperature=0,
    max_tokens=1000
)


print(response.choices[0].message.content)