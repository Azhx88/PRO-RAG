from groq import Groq
from config import settings

client = Groq(api_key=settings.groq_api_key)

def call_groq(prompt: str, system: str = "You are a helpful assistant.", max_tokens: int = 2048) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.2
    )
    return response.choices[0].message.content.strip()
