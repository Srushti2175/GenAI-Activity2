import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(f"API key loaded: {bool(api_key)}")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

text = "g|Ðr` eoVr nÜXVr à{ejU nwpñVH$m _hmamï´> Am°aJ°{ZH$ $m{_ªJ \o$S>aoeZ, nwUo"
prompt = (
    "The following Marathi text is encoded in legacy Shree-Lipi / Shree-Dev font ASCII glyphs. "
    "Please decode/transliterate it into clean, proper Devanagari Unicode Marathi script:\n\n"
    f"Text: {text}\n\n"
    "Only output the converted Marathi Unicode text."
)

try:
    resp = model.generate_content(prompt)
    sys.stdout.reconfigure(encoding="utf-8")
    print("Decoded:")
    print(resp.text)
except Exception as e:
    print(f"Error: {e}")
