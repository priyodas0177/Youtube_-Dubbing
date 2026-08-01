from openai import OpenAI


client = OpenAI(
    api_key="YOUR_KEY",
    base_url="YOUR_BASE_URL"
)


response = client.chat.completions.create(

    model="YOUR_MODEL",

    messages=[
        {
            "role":"user",
            "content":"Translate hello into Bangla"
        }
    ]

)


print(
    response.choices[0].message.content
)