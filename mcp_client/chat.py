"""
Interactive chat session for the MCP client.

This module provides a simple command-line chat interface that sends
user queries to a handler (OpenAIQueryHandler) and displays responses.
"""


async def run_chat(handler) -> None:
    """
    Run an interactive chat session.

    This function:
        1. Prompts the user for input
        2. Sends the input to the handler for processing
        3. Displays the response
        4. Repeats until the user types 'quit'

    Args:
        handler: An object with a process_query(str) async method
                 (typically OpenAIQueryHandler)
    """
    print("\nMCP Chat Started!")
    print("Type your questions or 'quit' to exit.\n")

    while True:
        try:
            # Get user input
            # The ':=' walrus operator assigns the stripped input to 'query'
            # and the 'if not' checks if it's empty
            if not (query := input("You: ").strip()):
                continue  # Skip empty input

            # Check for exit command
            if query.lower() == "quit":
                break

            # Process the query and display the response
            response = await handler.process_query(query)
            print(f"\n{response}\n")

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\n")
            break
        except Exception as e:
            print(f"\nError: {e}\n")

    print("Goodbye!")
