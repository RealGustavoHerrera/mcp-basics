# MCP Client Tutorial

A minimal example of building an MCP (Model Context Protocol) client and server in Python. This tutorial teaches you how to create AI applications that can use external tools.

## What is MCP?

MCP (Model Context Protocol) is a standard for connecting AI models to external tools and data. Think of it as a way to give your AI superpowers - instead of just chatting, it can:

- **Call tools** - Execute functions like searching, calculating, or querying databases
- **Use prompts** - Access pre-defined prompt templates
- **Read resources** - Access files, APIs, or other data sources

## Project Structure

```
mcp_client/
├── mcp_client/              # The client package
│   ├── __init__.py          # Package marker
│   ├── __main__.py          # Entry point (python -m mcp_client)
│   ├── cli.py               # Command-line argument parsing
│   ├── mcp_client.py        # Core client logic
│   ├── handlers.py          # OpenAI integration
│   └── chat.py              # Interactive chat loop
├── mcp_server/              # Example server
│   ├── mcp_server.py        # Server with tools, prompts, resources
│   └── greeting.txt         # Sample resource file
├── .env                     # Your OpenAI API key (create this)
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## How It Works

```
┌─────────────┐     stdio      ┌─────────────┐
│  MCP Client │ ◄────────────► │  MCP Server │
│  (Python)   │   JSON-RPC     │  (Python)   │
└──────┬──────┘                └─────────────┘
       │
       │ API calls
       ▼
┌─────────────┐
│   OpenAI    │
│   (GPT-4o)  │
└─────────────┘
```

1. The **client** starts the **server** as a subprocess
2. They communicate via JSON-RPC over stdin/stdout
3. The client asks OpenAI questions, providing available tools
4. When OpenAI wants to use a tool, the client calls it via MCP
5. Results are sent back to OpenAI for a final response

## Setup

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up your OpenAI API key

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your-api-key-here
```

Get your API key from: https://platform.openai.com/api-keys

## Usage

### List server capabilities

See what tools, prompts, and resources the server exposes:

```bash
python3 -m mcp_client mcp_server/mcp_server.py --members
```

Output:
```
MCP Server Members
==================================================

TOOLS (1):
------------------------------
  > echo - Echo back the provided message.

PROMPTS (1):
------------------------------
  > greeting_prompt - A prompt template for greeting someone kindly.

RESOURCES (1):
------------------------------
  > file://./greeting.txt - Serve the contents of greeting.txt as a resource.

==================================================
```

### Start an AI chat

Chat with an AI that can use the server's tools:

```bash
python3 -m mcp_client mcp_server/mcp_server.py --chat
```

Example conversation:
```
MCP Chat Started!
Type your questions or 'quit' to exit.

You: Can you echo "Hello MCP!"

[Used echo({'message': 'Hello MCP!'})]
Assistant: Hello MCP!

You: quit
Goodbye!
```

## Understanding the Code

### The Server (mcp_server/mcp_server.py)

The server uses `FastMCP` to expose capabilities:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my_server")

@mcp.tool()
async def echo(message: str) -> str:
    """Echo back the provided message."""
    return message
```

- `@mcp.tool()` - Registers a function as a callable tool
- `@mcp.prompt()` - Registers a prompt template
- `@mcp.resource("uri")` - Registers a data resource

### The Client (mcp_client/mcp_client.py)

The client connects to the server using async context managers:

```python
async with MCPClient("path/to/server.py") as client:
    await client.run_chat()
```

Key concepts:
- **AsyncExitStack** - Manages cleanup of multiple async resources
- **stdio_client** - Spawns server and creates communication streams
- **ClientSession** - Handles MCP protocol messages

### The AI Integration (mcp_client/handlers.py)

Bridges OpenAI with MCP tools:

1. Fetches available tools from MCP server
2. Sends user query to OpenAI with tool definitions
3. If OpenAI requests a tool, executes it via MCP
4. Returns final response to user

## Key Python Concepts Used

This tutorial uses some Python features that may be unfamiliar:

### Async/Await
```python
async def my_function():
    result = await some_async_operation()
```
Allows non-blocking I/O operations. The `await` keyword pauses until the operation completes.

### Context Managers
```python
async with MCPClient(...) as client:
    # client is set up
    ...
# client is automatically cleaned up
```
Ensures resources are properly initialized and cleaned up, even if errors occur.

### The Walrus Operator `:=`
```python
if not (api_key := os.getenv("KEY")):
    raise Error("Missing key")
```
Assigns a value and uses it in the same expression. Equivalent to:
```python
api_key = os.getenv("KEY")
if not api_key:
    raise Error("Missing key")
```

### Type Hints
```python
def echo(message: str) -> str:
```
Documents that `message` should be a string and the function returns a string. Python doesn't enforce these, but they help readability and IDE support.

## Next Steps

Now that you understand the basics, try:

1. **Add a new tool** - Edit `mcp_server.py` to add a tool that does something useful (e.g., get weather, search files)
2. **Add conversation memory** - Modify `handlers.py` to remember previous messages
3. **Try a different AI** - Replace OpenAI with Anthropic's Claude or a local model

## Learn More

- [MCP Documentation](https://modelcontextprotocol.io/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)