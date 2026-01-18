"""
Core MCP Client implementation.

This module contains the MCPClient class which manages the connection to an
MCP server. It handles starting the server subprocess, establishing
communication, and cleaning up resources.

Key concepts used:
    - Async context manager: Allows using 'async with MCPClient(...) as client:'
    - AsyncExitStack: Manages multiple async resources and their cleanup
    - stdio transport: Communication via standard input/output streams
"""
import sys
from contextlib import AsyncExitStack
from typing import Any, Awaitable, Callable

from mcp import ClientSession, stdio_client, StdioServerParameters

from mcp_client import chat
from mcp_client.handlers import OpenAIQueryHandler


class MCPClient:
    """
    MCP Client that connects to and communicates with an MCP server.

    Usage:
        async with MCPClient("path/to/server.py") as client:
            await client.list_all_members()
            # or
            await client.run_chat()

    The 'async with' pattern ensures the server is properly started and
    cleaned up, even if errors occur.
    """

    def __init__(self, server_path: str):
        """
        Initialize the MCP client.

        Args:
            server_path: Path to the MCP server Python script
        """
        self.server_path = server_path
        # These will be set when entering the context manager
        self.client_session: ClientSession | None = None
        self.exit_stack: AsyncExitStack | None = None

    async def __aenter__(self) -> "MCPClient":
        """
        Set up the MCP connection when entering 'async with' block.

        This method:
            1. Starts the MCP server as a subprocess
            2. Establishes stdio communication streams
            3. Creates a ClientSession for MCP protocol messages
            4. Performs the MCP initialization handshake

        Returns:
            self: The configured MCPClient instance
        """
        # AsyncExitStack manages cleanup of multiple async context managers.
        # Think of it as a stack of resources that need to be closed in
        # reverse order (last opened = first closed).
        self.exit_stack = AsyncExitStack()
        await self.exit_stack.__aenter__()

        # Step 1: Start the MCP server subprocess
        # stdio_client spawns the server and gives us read/write streams
        # enter_async_context() registers it for automatic cleanup later
        read, write = await self.exit_stack.enter_async_context(
            stdio_client(
                server=StdioServerParameters(
                    command=sys.executable,  # Uses the current Python interpreter
                    args=[self.server_path],  # The server script to run
                    env=None,  # Inherit current environment variables
                )
            )
        )

        # Step 2: Create an MCP session over those streams
        # ClientSession handles the MCP protocol (JSON-RPC messages)
        self.client_session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )

        # Step 3: Perform the MCP handshake
        # This exchanges capabilities between client and server
        await self.client_session.initialize()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up resources when exiting 'async with' block.

        The AsyncExitStack automatically closes everything in reverse order:
            1. First: Close the ClientSession
            2. Then: Terminate the server subprocess

        Args:
            exc_type: Exception type if an error occurred, else None
            exc_val: Exception value if an error occurred, else None
            exc_tb: Exception traceback if an error occurred, else None
        """
        if self.exit_stack:
            await self.exit_stack.__aexit__(exc_type, exc_val, exc_tb)

    async def list_all_members(self) -> None:
        """
        List all tools, prompts, and resources available on the MCP server.

        MCP servers expose three types of members:
            - Tools: Functions the AI can call (like 'echo', 'search', etc.)
            - Prompts: Pre-defined prompt templates
            - Resources: Data the server can provide (files, API data, etc.)
        """
        print("MCP Server Members")
        print("=" * 50)

        # Map section names to their listing methods
        sections = {
            "tools": self.client_session.list_tools,
            "prompts": self.client_session.list_prompts,
            "resources": self.client_session.list_resources,
        }

        for section_name, list_method in sections.items():
            await self._list_section(section_name, list_method)

        print("\n" + "=" * 50)

    async def _list_section(
        self,
        section: str,
        list_method: Callable[[], Awaitable[Any]],
    ) -> None:
        """
        Helper to list and format one section of MCP members.

        Args:
            section: Name of the section ('tools', 'prompts', or 'resources')
            list_method: Async method to call to get the list
        """
        try:
            # Call the listing method and get items from the response
            # getattr(response, 'tools') is like response.tools
            response = await list_method()
            items = getattr(response, section)

            if items:
                print(f"\n{section.upper()} ({len(items)}):")
                print("-" * 30)
                for item in items:
                    description = item.description or "No description"
                    print(f"  > {item.name} - {description}")
            else:
                print(f"\n{section.upper()}: None available")
        except Exception as e:
            print(f"\n{section.upper()}: Error - {e}")

    async def run_chat(self) -> None:
        """
        Start an interactive AI chat session with MCP tool integration.

        This creates an OpenAI-powered chat that can use the MCP server's
        tools to answer questions. For example, if the server has an 'echo'
        tool, the AI can decide to use it when appropriate.
        """
        try:
            handler = OpenAIQueryHandler(self.client_session)
            await chat.run_chat(handler)
        except RuntimeError as e:
            print(e)
