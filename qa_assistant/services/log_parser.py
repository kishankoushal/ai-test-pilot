from openai import OpenAI
from utils.config import OPENAI_API_KEY

def summarize_log(log: str) -> str:
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": f"Summarize this failure log:\n{log}"}]
    )
    return response.choices[0].message.content
