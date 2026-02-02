"""Check available Gemini models"""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
    
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    print("Available Gemini models:")
    print("=" * 60)
    
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"✓ {model.name}")
            print(f"  Display name: {model.display_name}")
            print(f"  Description: {model.description[:80]}...")
            print()
    
except ImportError:
    print("google-generativeai not installed. Trying langchain approach...")
    
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    # Try common model names
    models_to_test = [
        "gemini-1.5-flash",
        "gemini-1.5-pro", 
        "gemini-pro",
        "gemini-1.0-pro",
        "gemini-1.5-flash-001",
        "gemini-1.5-pro-001",
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro",
        "models/gemini-pro",
        "models/gemini-1.0-pro",
        "models/gemini-1.5-flash-001",
        "models/gemini-1.5-pro-001"
    ]
    
    print("Testing model names with LangChain:")
    print("=" * 60)
    
    for model_name in models_to_test:
        try:
            llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
            response = llm.invoke("Say 'ok'")
            print(f"✓ {model_name} - WORKS")
        except Exception as e:
            print(f"✗ {model_name} - {str(e)[:60]}")
