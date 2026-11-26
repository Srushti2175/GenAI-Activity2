import os
from dotenv import load_dotenv

# Load all variables from .env into environment
load_dotenv()

class Config:
    # Flask session secret key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'krishi-sakhi-dev-secret-key'

    # Groq AI API (Primary Chat LLM)
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    GROQ_MODEL   = os.environ.get('GROQ_MODEL', 'openai/gpt-oss-120b')

    # Google Gemini API (Optional: used for FAISS query embeddings if valid AIza key is set)
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    GEMINI_MODEL   = os.environ.get('GEMINI_MODEL', 'gemini-flash-lite-latest')

    # Default UI / response language
    DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'mr')

    # Safety: warn at startup if Groq key is missing
    @classmethod
    def validate(cls):
        if not cls.GROQ_API_KEY or cls.GROQ_API_KEY == 'your_groq_api_key_here':
            print(
                "\n[WARNING] GROQ_API_KEY is not set in your .env file.\n"
                "  The chatbot will use demo responses until a key is added.\n"
                "  Get a free key at: https://console.groq.com/keys\n"
            )
            return False
        return True
