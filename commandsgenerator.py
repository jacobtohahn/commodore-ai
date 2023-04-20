class CommandsGenerator:
    """
    A class for generating the commands available to the AI
    """
    def __init__(self):
        self.commands = []
        self.command_format = '{"command_name": {"argument": "value"}}'
        
    def add_command(self, command: str) -> None:
        self.commands.append(command)

    # def get_commands(self) -> str:
    #     commands_list = ""
    #     for command in self.commands:
    #         commands_list += f"{command}\n"
    #     commands_list.strip()

        # return commands_list