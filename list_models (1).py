import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY or API_KEY == "your_gemini_api_key_here":
    print("API Key not set.")
else:
    genai.configure(api_key=API_KEY)
    print("Available GenerateContent models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
