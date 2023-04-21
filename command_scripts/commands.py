"""Module for adding commands to the commands list"""
from command_scripts.commandsgenerator import CommandsGenerator

commands_generator = CommandsGenerator()

def prepare_commands_list() -> None:
    """
    Prepare the commands list by adding available commands
    This will be overhauled in the future to add commands from a list
    """
    commands_generator.add_command(
    ["Read an existing file", "read_file", {"file": "<file_name>"}]
    )
    commands_generator.add_command(
    ["Write to a file and create it if it doesn't exist",
     "write_file",
     {"file": "<file_name>", "text": "<text_to_write>"}]
    )
    commands_generator.add_command(
    ["Append to a file", "append_file", {"file": "<file_name>", "text": "<text_to_append>"}
    ])
    commands_generator.add_command(
    ["Delete a file", "delete_file", {"file": "<file_name>"}
    ])
    commands_generator.add_command(
    ["Make a new directory", "create_directory", {"directory": "<directory>"}
    ])
    commands_generator.add_command(
    ["Remove an existing directory", "remove_directory", {"directory": "<directory>"}
    ])
    commands_generator.add_command(
    ["Move an existing directory",
     "move_directory",
     {"directory": "<source>", "destination": "<destination>"}
    ])
    commands_generator.add_command(
    ["List all in all directories", "list_files", {}
    ])
    commands_generator.add_command(
    ["Search Google for a search phrase", "google", {"search": "<search_term>"}
    ])
    commands_generator.add_command(
    ["Browse a website URL with a question about the page",
     "browse_website",
     {"url": "<url_to_browse>", "search": "<general_question_about_website>"}
    ])
    commands_generator.add_command(
    ["No Command", "no_command", {}
    ])
