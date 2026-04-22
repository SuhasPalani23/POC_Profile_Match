"""LLM service — powered by OpenAI."""

from openai import OpenAI
from config import Config
import json
import re


class LLMService:
    """Generic LLM wrapper, using OpenAI GPT instances."""

    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"

    def _extract_json(self, text):
        try:
            text = re.sub(r"```json|```", "", text).strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                start = text.find("[")
                end = text.rfind("]") + 1
                if start == -1 or end == 0:
                    return None
            json_str = text[start:end]
            return json.loads(json_str)
        except Exception as e:
            print("JSON extraction error:", e)
            return None

    def generate_json(self, prompt: str):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            return self._extract_json(response.choices[0].message.content)
        except Exception as e:
            print(f"LLM Error: {e}")
            return None

