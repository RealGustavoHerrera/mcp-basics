"""
OpenAI integration for processing queries with MCP tool support.

This module bridges OpenAI's chat API with MCP tools. When OpenAI decides
to use a tool, this handler executes it via the MCP server and returns
the result.

Key concept - Tool Calling Flow:
    1. User asks a question
    2. OpenAI receives the question + list of available tools
    3. OpenAI may decide to call one or more tools
    4. We execute those tools via MCP and send results back to OpenAI
    5. OpenAI generates a final response using the tool results
"""
import json
import os

from dotenv import load_dotenv
from mcp import ClientSession
from openai import OpenAI

# Load environment variables from .env file (contains OPENAI_API_KEY)
load_dotenv()

# Model configuration - gpt-4o-mini is fast and cost-effective
MODEL = "gpt-4o-mini"
MAX_TOKENS = 1000


class OpenAIQueryHandler:
    """
    Handles queries by sending them to OpenAI with MCP tool integration.

    This class:
        - Fetches available tools from the MCP server
        - Sends queries to OpenAI with tool definitions
        - Executes any tools that OpenAI requests
        - Returns the final response
    """

    def __init__(self, client_session: ClientSession):
        """
        Initialize the handler with an MCP client session.

        Args:
            client_session: Active MCP ClientSession for tool execution

        Raises:
            RuntimeError: If OPENAI_API_KEY environment variable is not set
        """
        self.client_session = client_session

        # The ':=' is the "walrus operator" - it assigns and returns the value
        # This is equivalent to:
        #     api_key = os.getenv("OPENAI_API_KEY")
        #     if not api_key:
        if not (api_key := os.getenv("OPENAI_API_KEY")):
            raise RuntimeError(
                "Error: OPENAI_API_KEY environment variable not set. "
                "Add it to your .env file."
            )

        self.openai = OpenAI(api_key=api_key)

    async def process_query(self, query: str) -> str:
        """
        Process a user query using OpenAI, potentially calling MCP tools.

        Args:
            query: The user's question or request

        Returns:
            The AI's response, including any tool usage information
        """
        # Build the conversation with the user's message
        messages = [{"role": "user", "content": query}]

        # Send to OpenAI with available tools
        # OpenAI will decide whether to use any tools based on the query
        initial_response = self.openai.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=messages,
            tools=await self._get_tools(),  # MCP tools formatted for OpenAI
        )

        current_message = initial_response.choices[0].message
        result_parts = []

        # Collect any text content from the response
        if current_message.content:
            result_parts.append(current_message.content)

        # Check if OpenAI wants to call any tools
        # The ':=' walrus operator assigns tool_calls and checks if it's truthy
        if tool_calls := current_message.tool_calls:
            # Add assistant's response (with tool calls) to conversation history
            messages.append({
                "role": "assistant",
                "content": current_message.content or "",
                "tool_calls": tool_calls,
            })

            # Execute each tool that OpenAI requested
            for tool_call in tool_calls:
                tool_result = await self._execute_tool(tool_call)
                result_parts.append(tool_result["log"])  # Show what tool was used
                messages.append(tool_result["message"])  # Add result to conversation

            # Get OpenAI's final response after seeing tool results
            final_response = self.openai.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=messages,
            )

            if content := final_response.choices[0].message.content:
                result_parts.append(content)

        return "Assistant: " + "\n".join(result_parts)

    async def _get_tools(self) -> list:
        """
        Get MCP tools formatted for OpenAI's tool calling API.

        OpenAI expects tools in a specific format with type, name,
        description, and JSON schema for parameters.

        Returns:
            List of tool definitions in OpenAI's expected format
        """
        response = await self.client_session.list_tools()

        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "No description",
                    # inputSchema defines the tool's parameters as JSON Schema
                    "parameters": getattr(
                        tool,
                        "inputSchema",
                        {"type": "object", "properties": {}},
                    ),
                },
            }
            for tool in response.tools
        ]

    async def _execute_tool(self, tool_call) -> dict:
        """
        Execute an MCP tool and return the result.

        Args:
            tool_call: OpenAI's tool call object containing function name and args

        Returns:
            Dict with 'log' (human-readable) and 'message' (for OpenAI)
        """
        tool_name = tool_call.function.name
        # Parse the JSON arguments string into a Python dict
        tool_args = json.loads(tool_call.function.arguments or "{}")

        try:
            # Call the tool via MCP
            result = await self.client_session.call_tool(tool_name, tool_args)
            # Extract text content from the result
            content = result.content[0].text if result.content else ""
            log = f"[Used {tool_name}({tool_args})]"
        except Exception as e:
            content = f"Error: {e}"
            log = f"[Tool error: {e}]"

        return {
            "log": log,  # Shown to user to indicate tool usage
            "message": {
                "role": "tool",
                "tool_call_id": tool_call.id,  # Links result to the tool call
                "content": content,
            },
        }
