import streamlit as st
import asyncio
import json
import os
import re
from openai import AsyncOpenAI

# 1. Strict sequence array constraint (with Tamil second)
EXACT_LANGUAGE_SEQUENCE = ["Malayalam", "Tamil", "Kannada", "Telugu", "Marathi", "Hindi"]

st.set_page_config(page_title="AI Open Language Translator", page_icon="🌐", layout="centered")
st.title("🌐 AI Open Language Translator")
st.caption("Resilient OpenRouter Dynamic Tier | Sequence: Malayalam ➡️ Tamil ➡️ Kannada ➡️ Telugu ➡️ Marathi ➡️ Hindi")

# Initialize the OpenRouter client globally inside Streamlit's engine
if "openrouter_client" not in st.session_state:
    st.session_state.openrouter_client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY")
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messaging entries
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Core translation function leveraging the openrouter/free layer
async def execute_direct_translation(text: str) -> tuple[str, str]:
    if not os.environ.get("OPENROUTER_API_KEY"):
        return "⚠️ **Configuration Error:** `OPENROUTER_API_KEY` environment variable is missing. Please set it before running the app.", "None"

    system_prompt = """You are a professional localized interpreter. Your sole task is to process the input text.
Provide the accurate translation or conversational equivalent into these six languages: Malayalam, Tamil, Kannada, Telugu, Marathi, and Hindi.

Formatting Guidelines:
- Use the proper native script of each language (e.g., Devanagari script for Marathi and Hindi).
- Right next to the native script, include the phonetic Latin/English pronunciation inside parentheses.
- Context Rule: If the user text is an inquiry like 'how do I answer X' or 'how do I respond to Y', do not translate that phrase literally. Instead, translate the actual answers or responses to X or Y.

You MUST return strictly a raw, valid JSON object mapping the exact language names to their translations. Do not include any markdown fences or wrap text outside the JSON structure blocks.
Example shape:
{
    "Malayalam": "Native Script (Phonetic)",
    "Tamil": "Native Script (Phonetic)",
    "Kannada": "Native Script (Phonetic)",
    "Telugu": "Native Script (Phonetic)",
    "Marathi": "Native Script (Phonetic)",
    "Hindi": "Native Script (Phonetic)"
}"""

    # Targeting 'openrouter/free' lets OpenRouter auto-load balance across available free models dynamically
    response = await st.session_state.openrouter_client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.0
    )
    
    # Extract the actual model path string used by OpenRouter at runtime
    actual_model_used = getattr(response, 'model', 'Unknown Free Model')
    
    raw_text = response.choices[0].message.content.strip()
    
    # Advanced extraction tool to cleanly strip away markdown code blocks if the model emits them
    if "```" in raw_text:
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            raw_text = json_match.group(0)
            
    raw_text = raw_text.strip()
    if raw_text.startswith("json"):
        raw_text = raw_text.split("json", 1)[1].strip()

    raw_data = json.loads(raw_text)
    
    # Build a clean Markdown table enforcing the exact sequence order
    markdown_table = "| Language | Translation |\n| :--- | :--- |\n"
    for lang in EXACT_LANGUAGE_SEQUENCE:
        translation = raw_data.get(lang, "Translation unavailable")
        markdown_table += f"| **{lang}** | {translation} |\n"
        
    return markdown_table, actual_model_used

# Chat Interface Trigger Loop
if prompt := st.chat_input("Enter sentence or query (e.g., 'how do I answer how are you')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Routing query through available free resources..."):
            try:
                # Run the asynchronous OpenAI call inside Streamlit cleanly
                final_output, model_info = asyncio.run(execute_direct_translation(prompt))
                
                # Render the structural data grid table
                st.markdown(final_output)
                
                # Render a subtle visual badge underneath confirming the model identity
                st.caption(f"🤖 **Processed via:** `{model_info}`")
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"{final_output}\n\n*Processed via: `{model_info}`*"
                })
            except Exception as e:
                st.error(f"❌ Application Error: {str(e)}")