import os
import json
from typing import Dict
from fastmcp import FastMCP
from google import genai
from google.genai import types
from key import api_key

mcp = FastMCP("Dedicated-Regional-Translator")
gemini_client = genai.Client(api_key=api_key)

# Updated strict sequence array constraint adding Hindi at the end
EXACT_LANGUAGE_SEQUENCE = ["Malayalam", "Kannada", "Tamil", "Telugu", "Marathi", "Hindi"]

@mcp.tool()
def execute_indian_translation(text: str) -> Dict[str, str]:
    """
    Translates phrases, sentences, or conversational statements into Malayalam, Kannada, Tamil, Telugu, Marathi, and Hindi.
    Handles phrases like 'how do I answer/respond to X' by providing the appropriate responses natively.
    """
    prompt = f"""
    You are a professional localized interpreter. Your sole task is to process this input text:
    "{text}"
    
    Provide the accurate translation or conversational equivalent into these six languages in this EXACT sequence:
    1. Malayalam
    2. Kannada
    3. Tamil
    4. Telugu
    5. Marathi
    6. Hindi
    
    Formatting Guidelines:
    - Use the proper native script of each language (e.g., Devanagari script for Marathi and Hindi).
    - Right next to the native script, include the phonetic Latin/English pronunciation inside parentheses.
    - Context Rule: If the user text is an inquiry like 'how do I answer X' or 'how do I respond to Y', do not translate that phrase literally. Instead, translate the actual *answers or responses* to X or Y.
    
    You MUST return a valid, unquoted JSON object matching this schema shape perfectly:
    {{
        "Malayalam": "Native Script (Phonetic Transliteration)",
        "Kannada": "Native Script (Phonetic Transliteration)",
        "Tamil": "Native Script (Phonetic Transliteration)",
        "Telugu": "Native Script (Phonetic Transliteration)",
        "Marathi": "Native Script (Phonetic Transliteration)",
        "Hindi": "Native Script (Phonetic Transliteration)"
    }}
    """

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0, 
                response_mime_type="application/json"
            )
        )
        
        raw_data = json.loads(response.text)
        
        # Enforce sequence order preservation including Hindi before returning payload
        ordered_response = {lang: raw_data.get(lang, "Translation unavailable") for lang in EXACT_LANGUAGE_SEQUENCE}
        return ordered_response
        
    except Exception as e:
        return {"error": f"Server processing error: {str(e)}"}

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    mcp.run(transport="streamable-http", host=host, port=port, stateless_http=True)