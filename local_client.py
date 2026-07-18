import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from google import genai
from google.genai import types
from key import api_key

# Points to your local running FastMCP translator instance
LOCAL_URL = "http://localhost:8080/mcp"

# Initialize the Gemini Client
gemini_client = genai.Client(api_key=api_key)


# =====================================================================
# 🔥 FIX: Monkey patch google-genai bug handling boolean JSON schemas
# =====================================================================
from google.genai import _mcp_utils

original_filter = _mcp_utils._filter_to_supported_schema

def safe_filter_to_supported_schema(schema):
    # If the sub-element isn't a dictionary (like a boolean flag), return it as-is
    if not isinstance(schema, dict):
        return schema
    return original_filter(schema)

# Override the buggy SDK method with our safe one
_mcp_utils._filter_to_supported_schema = safe_filter_to_supported_schema
# =====================================================================


async def run_translator_client():
    print(f"Connecting to local Indian Translator MCP server at: {LOCAL_URL}...")
    
    async with streamablehttp_client(LOCAL_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as mcp_session:
            
            await mcp_session.initialize()
            print("Connected and MCP handshake complete.")

            prompt = (
                "Translate the sentence 'Where is the nearest railway station?' "
                "into Hindi, Tamil, and Kannada."
            )
            print(f"\nPrompting Gemini: '{prompt}'")

            # The patched schema parser now handles fastmcp safely here
            response = await gemini_client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    tools=[mcp_session]
                )
            )

            print("\n--- Gemini's Translated Output ---")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(run_translator_client())