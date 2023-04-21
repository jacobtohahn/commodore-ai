"""Module to define """
class CommandsGenerator:
    """
    A class for generating the commands available to the AI
    """
    def __init__(self):
        self.commands = []
        self.command_format = '{"command_name": {"argument": "value"}}'

    def add_command(self, command: str) -> None:
        """Add a command"""
        self.commands.append(command)

    def get_commands(self) -> str:
        """Get the currently available commands as a list"""
        commands_list = []
        for command in self.commands:
            commands_list.append(command)

        return commands_list
