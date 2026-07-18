import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Replace with your actual Lambda Function URL (ensure it retains the /mcp path)
LAMBDA_URL = "https://<YOUR_FUNCTION_URL_ID>.lambda-url.<REGION>.on.aws/mcp"

async def test_mcp_server():
    print(f"Connecting to MCP server at: {LAMBDA_URL}...")
    
    # 1. Establish the streamable HTTP transport channel
    async with streamablehttp_client(LAMBDA_URL) as (read_stream, write_stream, get_session_id):
        
        # 2. Open the standard MCP Client Session over the HTTP streams
        async with ClientSession(read_stream, write_stream) as session:
            
            # 3. Perform the protocol handshake
            await session.initialize()
            print("Successfully connected and initialized session!\n")
            
            # Optional: Print out the session ID assigned by the server
            if (session_id := get_session_id()) is not None:
                print(f"Active Session ID: {session_id}")

            # 4. List the available tools exposed by the Lambda function
            print("\n--- Fetching Available Tools ---")
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                print(f"🔧 Tool Name: {tool.name}")
                print(f"   Description: {tool.description}")
                print(f"   Schema: {tool.inputSchema}\n")

            # 5. Call the 'calculate_roi' tool defined in our server
            print("--- Executing Tool Call: calculate_roi ---")
            tool_arguments = {
                "principal": 10000.0,
                "rate": 7.5,
                "years": 5
            }
            
            print(f"Sending arguments: {tool_arguments}")
            
            # Fire the request straight to AWS Lambda
            result = await session.call_tool("calculate_roi", arguments=tool_arguments)
            
            print("\n--- Response From Server ---")
            print(result.content)

if __name__ == "__main__":
    # Run the async test block
    asyncio.run(test_mcp_server())