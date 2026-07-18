import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from google import genai
from google.genai import types

# 1. Configurations
LAMBDA_URL = "https://<YOUR_FUNCTION_URL_ID>.lambda-url.<REGION>.on.aws/mcp"
# Make sure you have export GEMINI_API_KEY="your-api-key" set in your terminal
gemini_client = genai.Client()

async def ask_gemini_with_mcp():
    print(f"Connecting to remote Lambda MCP server: {LAMBDA_URL}...")
    
    # 2. Open the connection stream to your serverless Lambda
    async with streamablehttp_client(LAMBDA_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as mcp_session:
            
            # Initialize the protocol handshake
            await mcp_session.initialize()
            print("MCP Session Initialized successfully.")

            # 3. Formulate a natural language prompt that requires the tool
            prompt = "I have a principal investment of $10,000 at a 7.5% simple rate for 5 years. Can you tell me what my ROI is?"
            print(f"\nPrompting Gemini: '{prompt}'")

            # 4. Call Gemini, feeding the live MCP session directly into the tools list
            response = await gemini_client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0, # Keep temp low for deterministic tool routing
                    tools=[mcp_session] # Gemini inspects the session schemas automatically
                )
            )

            print("\n--- Gemini's Final Response ---")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(ask_gemini_with_mcp())