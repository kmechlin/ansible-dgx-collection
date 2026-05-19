"""Minimal client for the vLLM OpenAI-compatible endpoint."""
import os

from openai import OpenAI

client = OpenAI(
    base_url=os.environ.get("OPENAI_BASE_URL", "http://dgx01:8000/v1"),
    api_key=os.environ["OPENAI_API_KEY"],
)

resp = client.chat.completions.create(
    model=os.environ.get("OPENAI_MODEL", "llama-3.1-8b"),
    messages=[
        {"role": "system", "content": "You are concise."},
        {"role": "user", "content": "Hello from vLLM!"},
    ],
)
print(resp.choices[0].message.content)
