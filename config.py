import os
from dotenv import load_dotenv

# Load all variables from .env into environment
load_dotenv()

class Config:
    # Flask session secret key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'krishi-sakhi-dev-secret-key'

    # Google Gemini API
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    GEMINI_MODEL   = os.environ.get('GEMINI_MODEL', 'gemini-flash-lite-latest')

    # Default UI / response language
    DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'mr')

    # Safety: warn at startup if key is missing
    @classmethod
    def validate(cls):
        if not cls.GEMINI_API_KEY or cls.GEMINI_API_KEY == 'your_gemini_api_key_here':
            print(
                "\n[WARNING] GEMINI_API_KEY is not set in your .env file.\n"
                "  The chatbot will use demo responses until a key is added.\n"
                "  Get a free key at: https://aistudio.google.com/app/apikey\n"
            )
            return False
        return True
