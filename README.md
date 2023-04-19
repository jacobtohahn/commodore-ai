# COMMODORE: An AI-based task completion agent

## Concept:

Commodore is a combination of two agents: a main agent which determines an action to perform based on a set of goals and the result of the previous action, and a command agent which translates the action into a command and executes it.

The main agent is given a list of constrains and capabilities, telling it what it can and cannot do. Some capabilities of the main agent include internet and filesystem access.

Based on these constraints and capabilities, the main agent uses natural language to describe a specific action to perform, e.g. "I will create a file called 'example.md' containing the text 'Hello, world!'".

This response is then passed to the command agent, which analyzes the natural language to output a command in a specified format. The command is parsed and executed, and the result of the command is fed back through the command agent, which describes the result in natural language. This natural language result is then given back to the main agent, which determines the next action to perform.

This structure ensures each agent is constrained in as few ways as possible and splits up the work so that each agent is only focused on one or two things at a time. For example, the only task of the main agent is to determine the next action, and the only tasks of the command agent are to either output a command or input a command result. The hope is that this structure allows each agent to stay focused and move towards the main goal without getting stuck.

Once the initial code has been written and tested, numerous improvements will be made, such as creating an agent dedicated to suggesting next actions and prioritizing them.
