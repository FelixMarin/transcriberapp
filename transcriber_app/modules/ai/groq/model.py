# transcriber_app/modules/ai/groq/model.py

from transcriber_app.modules.ai.base.model_interface import AIModel
from transcriber_app.modules.ai.groq.client import GroqClient


class GroqModel(AIModel):
    def __init__(self):
        self.client = GroqClient()

    def run(self, prompt: str):
        return self.client.chat(prompt)
