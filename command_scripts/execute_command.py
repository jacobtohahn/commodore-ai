from commands import commands_generator
from typing import Dict
from filesystem import *
from internet import *

def execute_command(command: str) -> str:
    command = Dict(command)

    command_name = list(command.keys())[0]
    arguments = list(command.keys())[1]

    command_found = False
    for commands in commands_generator.commands:
        if command_name in list(commands.keys())[0]:
            command_found = True
            break
        else:
            continue
    if not command_found:
        return "ERROR: COMMAND NOT FOUND"
    elif command_name == "read_file":
        return read_file(arguments("file"))
    elif command_name == "write_file":
        return write_file(arguments("file"), arguments("text"))
    elif command_name == "append_file":
        return append_file(arguments("file"), arguments("text"))
    elif command_name == "delete_file":
        return delete_file(arguments("file"))
    elif command_name == "create_directory":
        return create_directory(arguments("directory"))
    elif command_name == "remove_directory":
        return remove_directory(arguments("directory"))
    elif command_name == "move_directory":
        return move_directory(arguments("directory"), arguments("destination"))
    elif command_name == "list_files":
        return list_files()
    elif command_name == "google":
        return google(arguments("search"))
    elif command_name == "browse_website":
        return browse_website(arguments("url"))
    elif command_name == "no_command":
        return "ERROR: COMMAND NOT FOUND"
    
    
