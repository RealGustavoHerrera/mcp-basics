"""
Example MCP Server using FastMCP.

This is a minimal MCP server that demonstrates the three types of
things an MCP server can expose:

    1. Tools - Functions that AI can call (like 'echo')
    2. Prompts - Pre-defined prompt templates
    3. Resources - Data the server can provide (like files)

The server communicates via stdio (standard input/output), which means
the client starts this script as a subprocess and sends/receives
JSON-RPC messages through stdin/stdout.
"""
from mcp.server.fastmcp import FastMCP

# Create an MCP server instance
# The name "mcp_server" is used for identification in logs
mcp = FastMCP("mcp_server")


# =============================================================================
# TOOLS
# Tools are functions that the AI can call. The @mcp.tool() decorator
# registers this function as an available tool.
# =============================================================================

@mcp.tool()
async def echo(message: str) -> str:
    """Echo back the provided message."""
    return message


# =============================================================================
# PROMPTS
# Prompts are templates that help structure AI interactions.
# They can include dynamic parameters.
# =============================================================================

@mcp.prompt()
async def greeting_prompt(name: str) -> str:
    """A prompt template for greeting someone kindly."""
    return f"Greet {name} kindly."


# =============================================================================
# RESOURCES
# Resources provide data to the client. They're identified by URIs.
# Unlike tools, resources are for reading data, not performing actions.
# =============================================================================

@mcp.resource("file://./greeting.txt")
def greeting_file() -> str:
    """Serve the contents of greeting.txt as a resource."""
    with open("mcp_server/greeting.txt", "r", encoding="utf-8") as file:
        return file.read()


# =============================================================================
# MAIN
# Start the server when this script is run directly.
# =============================================================================

if __name__ == "__main__":
    # Run the server using stdio transport
    # This means it reads from stdin and writes to stdout
    # The client will spawn this as a subprocess and communicate via pipes
    mcp.run(transport="stdio")
