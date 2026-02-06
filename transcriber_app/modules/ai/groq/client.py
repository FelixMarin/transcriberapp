# transcriber_app/modules/ai/groq/client.py

import requests
from transcriber_app.config import GROQ_API_KEY


class GroqClient:
    URL = "https://api.groq.com/openai/v1/chat/completions"

    def chat(self, prompt: str, model="llama3-70b"):
        resp = requests.post(
            self.URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}]}
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
