import streamlit as st
import asyncio
import json
from google import genai
from google.genai import types
from key import api_key


# Define our strict sequence array constraint
EXACT_LANGUAGE_SEQUENCE = ["Malayalam", "Kannada", "Tamil", "Telugu", "Marathi", "Hindi"]

st.set_page_config(page_title="Regional Language Interface", page_icon="🌐", layout="centered")
st.title("🌐 Regional Indian Language Interface")
st.caption("Outputs locked to: Malayalam ➡️ Kannada ➡️ Tamil ➡️ Telugu ➡️ Marathi ➡️ Hindi")

# Initialize the Gemini Client globally inside Streamlit's engine
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = genai.Client(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messaging entries
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Core translation function leveraging Gemini directly inside the app thread
async def execute_direct_translation(text: str) -> str:
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

    # Call the model directly over the async client pipeline
    response = await st.session_state.gemini_client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0, 
            response_mime_type="application/json"
        )
    )
    
    raw_data = json.loads(response.text)
    
    # Build a clean Markdown table enforcing the exact target order sequence
    markdown_table = "| Language | Translation |\n| :--- | :--- |\n"
    for lang in EXACT_LANGUAGE_SEQUENCE:
        translation = raw_data.get(lang, "Translation unavailable")
        markdown_table += f"| **{lang}** | {translation} |\n"
        
    return markdown_table

# Chat Interface Trigger Loop
if prompt := st.chat_input("Enter sentence or query (e.g., 'how do I answer how are you')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing regional translations directly via Gemini..."):
            try:
                # Run the simple asynchronous coroutine safely inside Streamlit
                final_output = asyncio.run(execute_direct_translation(prompt))
                st.markdown(final_output)
                st.session_state.messages.append({"role": "assistant", "content": final_output})
            except Exception as e:
                st.error(f"❌ Application Error: {str(e)}")