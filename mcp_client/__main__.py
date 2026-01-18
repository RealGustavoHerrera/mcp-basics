"""
Entry point for running the MCP client as a module.

Usage:
    python3 -m mcp_client <server_path> --chat
    python3 -m mcp_client <server_path> --members
"""
import asyncio

from mcp_client.cli import parse_args
from mcp_client.mcp_client import MCPClient


async def main() -> None:
    """Run the MCP client with the specified command-line options."""
    args = parse_args()

    # Validate that the server script exists before trying to run it
    if not args.server_path.exists():
        print(f"Error: Server script '{args.server_path}' not found")
        return

    try:
        # The 'async with' syntax automatically calls __aenter__ and __aexit__
        # This ensures the MCP server process is properly started and cleaned up
        async with MCPClient(str(args.server_path)) as client:
            if args.members:
                await client.list_all_members()
            elif args.chat:
                await client.run_chat()
    except RuntimeError as e:
        print(e)


# This block runs when you execute: python3 -m mcp_client
if __name__ == "__main__":
    # asyncio.run() starts the async event loop and runs our main() coroutine
    asyncio.run(main())
