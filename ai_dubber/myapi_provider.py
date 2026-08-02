import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# LOAD API KEYS
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")


for key, value in {
    "NVIDIA_API_KEY": NVIDIA_API_KEY,
    "GROQ_API_KEY": GROQ_API_KEY,
    "OLLAMA_API_KEY": OLLAMA_API_KEY
}.items():
    if not value:
        raise ValueError(f"❌ {key} is not set in the environment variables.")


# API CLIENTS
clients = {

    "NVIDIA": OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=NVIDIA_API_KEY,
        timeout=90,
        max_retries=2
    ),


    "Groq": OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY,
        timeout=90,
        max_retries=2
    ),


    "Ollama": OpenAI(
        base_url="https://ollama.com/v1",
        api_key=OLLAMA_API_KEY,
        timeout=90,
        max_retries=2
    )
}

# GLOBAL MODEL PRIORITY
# Best → Worst


models_priority = [

    {
        "provider": "Groq",
        "model": "openai/gpt-oss-120b",
    },

    {
        "provider": "Ollama",
        "model": "gpt-oss:120b",
    },


    {
        "provider": "Groq",
        "model": "llama-3.3-70b-versatile",
    },

    {
        "provider": "NVIDIA",
        "model": "meta/llama-3.3-70b-instruct",
    },


    {
        "provider": "Ollama",
        "model": "nemotron-3-ultra",
    },


    {
        "provider": "Groq",
        "model": "qwen/qwen3.6-27b",
    },


    {
        "provider": "Ollama",
        "model": "gemma4:31b",
    },

    {
        "provider": "Groq",
        "model": "openai/gpt-oss-20b",
    },

    {
        "provider": "Ollama",
        "model": "gpt-oss:20b",
    },

    {
        "provider": "Groq",
        "model": "llama-3.1-8b-instant",
    }
]

def translate_with_fallback(system_prompt, user_prompt, json_mode=False):

    for item in models_priority:

        provider = item["provider"]
        model = item["model"]

        try:

            print(
                "\n=============================="
            )
            print(
                f"🤖 AI MODEL: {provider} -> {model}"
            )
            print(
                "=============================="
            )


            request_args = {

                "model": model,

                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],

                "temperature": 0.15,
                "top_p": 0.85,
                "max_tokens": 4096
            }


            if json_mode:
                request_args["response_format"] = {
                    "type": "json_object"
                }


            response = clients[provider].chat.completions.create(
                **request_args
            )

            print(
                f"✅ SUCCESS: {provider} -> {model}"
            )


            return response


        except Exception as e:

            print(
                f"❌ FAILED: {provider} -> {model}"
            )

            print(e)

            continue


    raise Exception(
        "All AI models failed"
    )