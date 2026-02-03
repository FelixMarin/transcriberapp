import google.generativeai as genai
from transcriber_app.config import GOOGLE_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)


class GeminiAgent:
    def __init__(
        self,
        model_name: str,
        system_prompt: str,
        temperature: float = 0.2,
        top_p: float = 0.9,
        top_k: int = 40,
        max_output_tokens: int = 4096,
    ):
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_output_tokens = max_output_tokens

        # El constructor AHORA es simple
        self._model = genai.GenerativeModel(self.model_name)

    def run(self, text: str) -> str:
        response = self._model.generate_content(
            text,
            system_instruction=self.system_prompt,
            generation_config={
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "max_output_tokens": self.max_output_tokens,
            },
        )

        return getattr(response, "text", "") or ""
