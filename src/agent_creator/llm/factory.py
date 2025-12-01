from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
from google import genai
from config import Config

class LLMClient(ABC):
    @abstractmethod
    def generate_json(self, prompt: str, system_instruction: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        pass


class GoogleLLMClient(LLMClient):
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)

    def generate_json(self, prompt: str, system_instruction: str, schema: Dict[str, Any]) -> Dict[str, Any]:

        # Use generate_content for google-genai SDK
        # Combine system instruction and prompt for simplicity or use config if available
        full_prompt = f"{system_instruction}\n\n{prompt}"
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt
        )

        try:
            text_response = response.text

            if "```json" in text_response:
                text_response = text_response.split("```json")[1].split("```")[0].strip()
            elif "```" in text_response:
                text_response = text_response.split("```")[1].split("```")[0].strip()

            parsed_json = json.loads(text_response)

            return {
                "parsed_json": parsed_json,
                "total_tokens": getattr(response, "usage", {}).get("total_tokens", 0),
                "cost_usd": 0.0,
                "model": self.model_name
            }

        except Exception as e:
            if isinstance(response, dict):
                return {
                    "parsed_json": response,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                    "model": self.model_name
                }
            raise ValueError(f"Failed to parse JSON from ADK response: {e}")


def create_llm_client(provider: str = None) -> LLMClient:
    if provider is None:
        provider = Config.LLM_PROVIDER
    
    if provider.lower() == "google":
        return GoogleLLMClient(api_key=Config.GOOGLE_API_KEY)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
