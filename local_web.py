import streamlit as st
import anyio
import concurrent.futures
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from google import genai
from google.genai import types
from key import api_key

# =====================================================================
# 🔥 FIX: Monkey patch google-genai bug handling boolean JSON schemas
# =====================================================================
from google.genai import _mcp_utils
original_filter = _mcp_utils._filter_to_supported_schema
def safe_filter_to_supported_schema(schema):
    if not isinstance(schema, dict): return schema
    return original_filter(schema)
_mcp_utils._filter_to_supported_schema = safe_filter_to_supported_schema
# =====================================================================

LOCAL_URL = "http://localhost:8080/mcp"

st.set_page_config(page_title="Language Interface", page_icon="🌐", layout="centered")
st.title("🌐 Language Interface")
st.caption("Outputs locked to: Malayalam ➡️ Kannada ➡️ Tamil ➡️ Telugu ➡️ Marathi ➡️ Hindi")

if "gemini_client" not in globals():
    gemini_client = genai.Client(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messaging entries
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

async def async_translation_worker(user_prompt, output_holder):
    async with streamablehttp_client(LOCAL_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as mcp_session:
            await mcp_session.initialize()
            
            # Formulate rigid operational layout logic containing Hindi at the end
            system_instruction = (
                "You are an interface router. Take the user prompt and pass it directly to the tool. "
                "Do not answer the user prompt yourself. Use the tool response to display a neat "
                "Markdown table layout containing the columns: 'Language' and 'Translation'. "
                "You must display the rows exactly in this order: Malayalam, Kannada, Tamil, Telugu, Marathi, Hindi."
            )
            
            response = await gemini_client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    system_instruction=system_instruction,
                    tools=[mcp_session]
                )
            )
            output_holder["text"] = response.text

def run_translation_pipeline(user_prompt):
    output_holder = {"text": None}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(lambda: anyio.run(async_translation_worker, user_prompt, output_holder))
        try:
            future.result()
        except BaseException as e:
            if output_holder["text"] is not None:
                return output_holder["text"]
            
            error_msg = str(e)
            if hasattr(e, 'exceptions') and e.exceptions:
                sub_errors = [f"{type(se).__name__}: {str(se)}" for se in e.exceptions]
                error_msg = " | ".join(sub_errors)
            raise RuntimeError(f"Pipeline error -> {error_msg}")

    return output_holder["text"]

# Chat Interface Trigger
if prompt := st.chat_input("Enter sentence or query (e.g., 'how do I answer how are you')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing regional data streams..."):
            try:
                final_output = run_translation_pipeline(prompt)
                st.markdown(final_output)
                st.session_state.messages.append({"role": "assistant", "content": final_output})
            except Exception as e:
                st.error(f"❌ {str(e)}")