import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

try:
    print("Łączenie z API Gemini...")
    client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))
    
    print("Dostępne modele generatywne to:\n")
    # Pobieramy listę modeli i filtrujemy tylko te, które wspierają generowanie tekstu
    for model in client.models.list():
        if "generateContent" in model.supported_actions:
            print(f"✅ {model.name}")
            
except Exception as e:
    print(f"Wystąpił błąd: {e}")