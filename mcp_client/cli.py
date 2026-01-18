"""
Command-line argument parsing for the MCP client.

This module uses Python's built-in argparse library to define and parse
command-line arguments. It's a standard way to create CLI tools in Python.
"""
import argparse
import pathlib


def parse_args():
    """
    Parse and return command-line arguments.

    Returns an object with these attributes:
        - server_path: Path to the MCP server script
        - members: True if --members flag was passed
        - chat: True if --chat flag was passed
    """
    parser = argparse.ArgumentParser(
        description="A minimal MCP client that connects to an MCP server"
    )

    # Positional argument: the path to the MCP server script
    # pathlib.Path automatically converts the string to a Path object
    parser.add_argument(
        "server_path",
        type=pathlib.Path,
        help="path to the MCP server script (e.g., mcp_server/mcp_server.py)",
    )

    # Mutually exclusive group: user must choose exactly one of these options
    # This prevents running both --members and --chat at the same time
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "--members",
        action="store_true",  # Sets args.members = True when flag is present
        help="list the MCP server's tools, prompts, and resources",
    )

    group.add_argument(
        "--chat",
        action="store_true",  # Sets args.chat = True when flag is present
        help="start an AI-powered chat with MCP server integration",
    )

    return parser.parse_args()
