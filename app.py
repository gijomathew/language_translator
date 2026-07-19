import streamlit as st
import asyncio
import json
import os
import re
from openai import AsyncOpenAI

# 1. Available languages repository
AVAILABLE_LANGUAGES = [
    "Malayalam", "Tamil", "Kannada", "Telugu", "Marathi", "Hindi",
    "Chinese", "Japanese", "Bengali", "Gujarati", "Punjabi", "Odia", 
    "Assamese", "Urdu", "English", "Spanish", "French", "German"
]

# 2. Strict default tracking sequence
DEFAULT_SEQUENCE = ["Malayalam", "Tamil", "Kannada", "Telugu", "Marathi", "Hindi"]

st.set_page_config(page_title="AI Language Translator", page_icon="🌐", layout="centered")
st.title("🌐 AI Language Translator")

# --- MOBILE-OPTIMIZED SIDEBAR CONFIGURATION ---
st.sidebar.header("⚙️ Translation Mode")

# NEW FEATURE: Select translation behavior direction
translation_mode = st.sidebar.radio(
    "Select Workflow Direction:",
    options=["English ➡️ Regional", "Detect Copy-Paste ➡️ English + Others"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.header("📱 Tap Target Languages")
st.sidebar.write("Toggle visibility using the touch-friendly pills below:")

# Maintain chosen language state dynamically in list order
selected_languages = []

for lang in AVAILABLE_LANGUAGES:
    # If in copy-paste mode, English must always be part of the target outputs
    if translation_mode == "Detect Copy-Paste ➡️ English + Others" and lang == "English":
        continue
        
    is_default = lang in DEFAULT_SEQUENCE
    if st.sidebar.toggle(f"📍 {lang}", value=is_default, key=f"toggle_{lang}"):
        selected_languages.append(lang)

# Force append English at the very top of output matrix if parsing an unknown foreign language input
if translation_mode == "Detect Copy-Paste ➡️ English + Others":
    selected_languages.insert(0, "English")

st.sidebar.markdown("---")

# Text input provider optimized for mobile keyboards
new_lang = st.sidebar.text_input("➕ Add a custom language:", placeholder="e.g., Arabic")
if st.sidebar.button("Add to List") and new_lang.strip():
    custom_lang = new_lang.strip().capitalize()
    if custom_lang not in AVAILABLE_LANGUAGES:
        AVAILABLE_LANGUAGES.append(custom_lang)
        st.rerun()

# Dynamic workflow text feedback
if selected_languages:
    st.caption(f"📱 **Active Mode:** `{translation_mode}` | **Pipeline:** {' ➡️ '.join(selected_languages)}")
else:
    st.caption("⚠️ **Active Pipeline:** No languages selected. Toggle options in the sidebar menu.")

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

# Core translation engine adjusting prompt behavior based on dynamic modes
async def execute_direct_translation(text: str, current_sequence: list, mode: str) -> tuple[str, str]:
    if not os.environ.get("OPENROUTER_API_KEY"):
        return "⚠️ **Configuration Error:** `OPENROUTER_API_KEY` environment variable is missing.", "None"
    
    if not current_sequence:
        return "⚠️ Please select at least one target language from the sidebar toggle settings.", "None"

    numbered_langs = "\n".join([f"{i+1}. {lang}" for i, lang in enumerate(current_sequence)])
    schema_shape = ",\n".join([f'    "{lang}": "Native Script / Character (Phonetic)"' for lang in current_sequence])

    # Dynamic system instruction branching based on selected UI mode toggle
    if mode == "English ➡️ Regional":
        system_prompt = f"""You are a professional localized interpreter. Your sole task is to process the input text.
Provide the accurate translation or conversational equivalent into these target languages in this EXACT sequence:
{numbered_langs}

Formatting Guidelines:
- Use the proper native script or native logographic characters of each language (e.g., Devanagari script for Hindi/Marathi, Hanzi characters for Chinese, Kanji/Kana for Japanese).
- Right next to the native script/character rendering, include the phonetic Latin/English pronunciation inside parentheses.
- Context Rule: If the user text is an inquiry like 'how do I answer X' or 'how do I respond to Y', do not translate that phrase literally. Instead, translate the actual answers or responses to X or Y.
"""
    else:
        # Instruction optimization for Copy-Pasted foreign texts
        system_prompt = f"""You are an advanced multilingual translation machine. The user will copy-paste text in any language.
Your task is to identify the source language, analyze it, and translate it accurately into these target languages in this EXACT sequence:
{numbered_langs}

Formatting Guidelines:
- For English, provide standard natural text without phonetics.
- For all other non-English target languages, use the proper native script/character rendering, and right next to it, include the phonetic Latin/English pronunciation inside parentheses.
- Translate the literal message meaning accurately, keeping context intact.
"""

    # Append structural formatting constraints to the chosen prompt rule branch
    system_prompt += f"""
You MUST return strictly a raw, valid JSON object matching this schema shape perfectly:
{{
{schema_shape}
}}"""

    response = await st.session_state.openrouter_client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.0
    )
    
    actual_model_used = getattr(response, 'model', 'Unknown Free Model')
    raw_text = response.choices[0].message.content.strip()
    
    if "```" in raw_text:
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            raw_text = json_match.group(0)
            
    raw_text = raw_text.strip()
    if raw_text.startswith("json"):
        raw_text = raw_text.split("json", 1)[1].strip()

    raw_data = json.loads(raw_text)
    
    # Build clean Markdown table mapping dynamic sequence
    markdown_table = "| Language | Translation |\n| :--- | :--- |\n"
    for lang in current_sequence:
        translation = raw_data.get(lang, "Translation unavailable")
        markdown_table += f"| **{lang}** | {translation} |\n"
        
    return markdown_table, actual_model_used

# Chat Interface Trigger Loop
if prompt := st.chat_input("Paste foreign text or enter query here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Routing query through dynamic model channels..."):
            try:
                # Pass mode selection parameter into translation processing routine
                final_output, model_info = asyncio.run(
                    execute_direct_translation(prompt, selected_languages, translation_mode)
                )
                
                st.markdown(final_output)
                st.caption(f"🤖 **Processed via:** `{model_info}`")
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"{final_output}\n\n*Processed via: `{model_info}`*"
                })
            except Exception as e:
                st.error(f"❌ Application Error: {str(e)}")