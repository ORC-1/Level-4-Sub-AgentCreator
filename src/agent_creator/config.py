import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    AGENT_MODEL = os.getenv("AGENT_MODEL", "gpt-4-turbo")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 4096))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
