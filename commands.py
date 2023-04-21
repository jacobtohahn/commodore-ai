from commandsgenerator import CommandsGenerator

commands_generator = CommandsGenerator()

def prepare_commands_list() -> None:
    commands_generator.add_command(
    ["Read File", "read_file", {"file": "<file_name>"}]
    )
    commands_generator.add_command(
    ["Write File", "write_file", {"file": "<file_name>", "text": "<text_to_write>"}]
    )
    commands_generator.add_command(
    ["Append to File", "append_file", {"file": "<file_name>", "text": "<text_to_append>"}
    ])
    commands_generator.add_command(
    ["Delete File", "delete_file", {"file": "<file_name>"}
    ])
    commands_generator.add_command(
    ["Create Directory", "create_directory", {"directory": "<directory>"}
    ])
    commands_generator.add_command(
    ["Remove Directory", "remove_directory", {"directory": "<directory>"}
    ])
    commands_generator.add_command(
    ["Move Directory", "move_directory", {"directory": "<source>", "destination": "<destination>"}
    ])
    commands_generator.add_command(
    ["List all Files", "list_files", {}
    ])
    commands_generator.add_command(
    ["Google Search", "google", {"search": "<search_term>"}
    ])
    commands_generator.add_command(
    ["Browse Website", "browse_website", {"url": "<url_to_browse>", "search": "<question_about_website>"}
    ])
    commands_generator.add_command(
    ["No Command", "no_command", {}
    ])