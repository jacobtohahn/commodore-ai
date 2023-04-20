from dotenv import load_dotenv
import os
import re
import openai
import pinecone
from collections import deque
from typing import Dict, List
import time
from constraints_capabilities import capabilities_generator
from commands import commands_generator, prepare_commands_list
from command_scripts.execute_command import execute_command

# Class for text colors
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Load default environment variables (.env)
load_dotenv()

# Engine configuration

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"

# Get GPT Model
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")

# Model configuration
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.0))

# Get Pinecone Info
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
assert PINECONE_API_KEY, "PINECONE_API_KEY environment variable is missing from .env"

PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
assert (
    PINECONE_ENVIRONMENT
), "PINECONE_ENVIRONMENT environment variable is missing from .env"

# Get the AI's name
COMMODORE_NAME = os.getenv("AI_NAME", "Commodore")

# Get Main Objective
OBJECTIVE = os.getenv("OBJECTIVE", "Research nuclear fusion")

# Get the AI's constraints and capabilities
constraints_capabilities = capabilities_generator.get_constraints_capabilities()

# Prepare commands list
prepare_commands_list()

# Pinecone namespaces are only compatible with ascii characters (used in query and upsert)
ASCII_ONLY = re.compile('[^\x00-\x7F]+')
OBJECTIVE_PINECONE_COMPAT = re.sub(ASCII_ONLY, '', OBJECTIVE)

# Get the first task to perform
INITIAL_TASK = os.getenv("INITIAL_TASK", 
                         os.getenv("FIRST_TASK", 
                                   "Determine the current status of nuclear fusion technology")
                        )

# Print the inital startup message
print(f"{bcolors.OKGREEN}{bcolors.BOLD}WELCOME TO COMMODORE!{bcolors.ENDC}")

# Check if we know what we are doing
assert OBJECTIVE, "OBJECTIVE environment variable is missing from .env. Cannot proceed."
assert INITIAL_TASK, "INITIAL_TASK environment variable is missing from .env. Cannot proceed."

# Print the AI configuration:
print(f"{bcolors.OKCYAN}Current AI configuration:{bcolors.ENDC}")
print(f"{COMMODORE_NAME} is an AI based on {OPENAI_API_MODEL} designed to {OBJECTIVE}.\n"
      f" To do this, it will first start by performing the following task:\n"
      f"{INITIAL_TASK}")

# Configure OpenAI and Pinecone
openai.api_key = OPENAI_API_KEY
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

# Create Pinecone index
table_name = "commodore-ai"
dimension = 1536
metric = "cosine"
pod_type = "p1"
if table_name not in pinecone.list_indexes():
    pinecone.create_index(
        table_name, dimension=dimension, metric=metric, pod_type=pod_type
    )

# Connect to the index
index = pinecone.Index(table_name)

# Clear previous memories
index.delete(delete_all=True, namespace=OBJECTIVE_PINECONE_COMPAT)

# Task storage supporting only a single instance of Commodore
class SingleTaskListStorage:
    def __init__(self):
        self.tasks = deque([])
        self.task_id_counter = 0

    def append(self, task: Dict):
        self.tasks.append(task)

    def replace(self, tasks: List[Dict]):
        self.tasks = deque(tasks)

    def popleft(self):
        return self.tasks.popleft()

    def is_empty(self):
        return False if self.tasks else True

    def next_task_id(self):
        self.task_id_counter += 1
        return self.task_id_counter

    def get_task_names(self):
        return [t["task_name"] for t in self.tasks]
    
# Initialize tasks storage
tasks_storage = SingleTaskListStorage()
    
# Get embedding for the text
def get_ada_embedding(text):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")[
        "data"
    ][0]["embedding"]

# Interface with the OpenAI API
def openai_call(
    prompt: str,
    model: str = OPENAI_API_MODEL,
    temperature: float = OPENAI_TEMPERATURE,
    max_tokens: int = 100,
):
    while True:
        try:
            if not model.startswith("gpt-"):
                # Use completion API
                response = openai.Completion.create(
                    engine=model,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                )
                return response.choices[0].text.strip()
            else:
                # Use chat completion API
                messages = [{"role": "system", "content": prompt}]
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    n=1,
                    stop=None,
                )
                return response.choices[0].message.content.strip()
        except openai.error.RateLimitError:
            print(
                "   *** The OpenAI API rate limit has been exceeded. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.Timeout:
            print(
                "   *** OpenAI API timeout occured. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.APIError:
            print(
                "   *** OpenAI API error occured. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.APIConnectionError:
            print(
                "   *** OpenAI API connection error occured. Check your network settings, proxy configuration, SSL certificates, or firewall rules. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.InvalidRequestError:
            print(
                "   *** OpenAI API invalid request. Check the documentation for the specific API method you are calling and make sure you are sending valid and complete parameters. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.ServiceUnavailableError:
            print(
                "   *** OpenAI API service unavailable. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        else:
            break

# Define the execution agent
def execution_agent(objective: str, task: str) -> str:
    """
    Executes a task based on the given objective and previous context.

    Args:
        objective (str): The objective or goal for the AI to perform the task.
        task (str): The task to be executed by the AI.

    Returns:
        str: The response generated by the AI for the given task.
    """
    
    context = context_agent(query=objective, top_results_num=5)
    prompt = f"""
    You are an AI who determines a single task to be executed based on the following objective: {objective}.
    Take into account these previously completed tasks: {context}.
    Your task: {task}
    Your response must be adhere exectly to the following constraints and capabilities:
    {constraints_capabilities}
    Do not generate a command.
    Only one action should be performed. Do not use the word "and" to split up actions.
    Only one subtask, like searching the internet or writing to a file, should be included in your response.
    For example: "Search the internet for..." or "Browse the webpage at the URL..."
    Response:"""
    return openai_call(prompt, max_tokens=2000)

# Get the top n completed tasks for the objective
def context_agent(query: str, top_results_num: int):
    """
    Retrieves context for a given query from an index of tasks.

    Args:
        query (str): The query or objective for retrieving context.
        top_results_num (int): The number of top results to retrieve.

    Returns:
        list: A list of tasks as context for the given query, sorted by relevance.

    """
    query_embedding = get_ada_embedding(query)
    results = index.query(query_embedding, top_k=top_results_num, include_metadata=True, namespace=OBJECTIVE_PINECONE_COMPAT)
    sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)
    return [(str(item.metadata["task"])) for item in sorted_results]

def command_translation_agent(command_prompt: str) -> str:
    context = context_agent(query=command_prompt, top_results_num=5)
    prompt = f"""You are an AI responsible for translating a desired action into a single command of a specified output format.
This one command should only perform one action.
Your output format, which you must exactly adhere to at all times, is as follows:
{commands_generator.command_format}
Do not omit any piece of this response format or add any text other than the response format.
The response should be all on one line.
These are your available commands:
{commands_generator.commands}.
You MUST use one command exclusively from the list provided above.
If the desired action does not seem to use a command available to you, use the command no_command.
Argument keys must be listed exactly as specified.
Take into account these previously completed tasks: {context}.
If the action to translate includes a website URL, use the "browse_website" command instead of "read_file".
If the action contains multiple steps, only translate the first task.
The desired action to translate into the response format is:
{command_prompt}"""
    return openai_call(prompt, max_tokens=2000)

def task_creation_agent(
    objective: str, result: Dict, task_description: str, task_list: List[str]
):
    context = context_agent(query=objective, top_results_num=5)
    prompt = f"""
    You are a task creation AI that uses the result of an execution agent to create new tasks, each performing a single action, with the following objective: {objective},
    Take into account these previously completed tasks: {context}.
    The last completed task has the result: {result}.
    This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join(task_list)}.
    Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks.
    Only one action should be performed per task.
    Include specifics and URLs in your response if applicable. Return the tasks as an array. Do not return a command."""
    response = openai_call(prompt)
    new_tasks = response.split("\n") if "\n" in response else [response]
    return [{"task_name": task_name} for task_name in new_tasks]

def prioritization_agent():
    task_names = tasks_storage.get_task_names()
    next_task_id = tasks_storage.next_task_id()
    prompt = f"""
    You are a task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}.
    Consider the ultimate objective of your team:{OBJECTIVE}.
    Do not remove any tasks. Return the result as a numbered list, like:
    #. First task
    #. Second task
    Start the task list with number {next_task_id}."""
    response = openai_call(prompt)
    new_tasks = response.split("\n") if "\n" in response else [response]
    new_tasks_list = []
    for task_string in new_tasks:
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            new_tasks_list.append({"task_id": task_id, "task_name": task_name})
    tasks_storage.replace(new_tasks_list)

# Add the initial task
initial_task = {
    "task_id": tasks_storage.next_task_id(),
    "task_name": INITIAL_TASK
}
tasks_storage.append(initial_task)

# Main loop
while True:
    # As long as there are tasks in the storage...
    if not tasks_storage.is_empty():
        # Print the task list
        print("\033[95m\033[1m" + "\n*****TASK LIST*****\n" + "\033[0m\033[0m")
        for t in tasks_storage.get_task_names():
            print(" • "+t)

        # Step 1: Pull the first incomplete task
        task = tasks_storage.popleft()
        print("\033[92m\033[1m" + "\n*****NEXT TASK*****\n" + "\033[0m\033[0m")
        print(task['task_name'])

        # Send to execution function to complete the task based on the context
        result = execution_agent(OBJECTIVE, task["task_name"])
        print("\033[93m\033[1m" + "\n*****ACTION*****\n" + "\033[0m\033[0m")
        print(result)

        # Step 2: Send natural language result to command translator
        command = command_translation_agent(result)
        print("\033[93m\033[1m" + "\n*****COMMAND*****\n" + "\033[0m\033[0m")

        # Step 3: Execute command
        loop_count = 0
        command_return = execute_command(command)
        while (str(command_return).startswith("COMMAND_ERROR:") | str(command_return).startswith("ERROR: INVALID ARGUMENTS")) and loop_count < 3:
            new_command = command_translation_agent(f"""
            The last command you entered, {command},
            which was generated based on the following request: {result},
            did not execute correctly and returned this error: {command_return}
            Please regenerate the command with the required modifications based on the commands list to fix the error.
            """)
            command_return = execute_command(new_command)
            loop_count += 1
        if loop_count >= 3:
            print("***************STUCK IN LOOP***************")
            print("EXITING...")
            exit()
        elif command_return == "ERROR: COMMAND NOT FOUND":
            command_result = """You this action is outside of your constraints or capabilities!\n
            Ensure you are working within your constraints and capabilities and try again."""
        else:
            command_result = command_return
        print(command)
        print("\033[93m\033[1m" + "\n*****COMMAND RESULT*****\n" + "\033[0m\033[0m")
        print(command_return)
        print(command_result)

        # Step 3: Enrich result and command and store in Pinecone
        ### NOT FINISHED ###
        enriched_result = {
            "data": f"{result}\n"
                    f"Command: {command}\n"
                    f"Command result: {command_result}"
        }  # This is where you should enrich the result if needed
        result_id = f"result_{task['task_id']}"
        vector = get_ada_embedding(
            enriched_result["data"]
        )  # get vector of the actual result extracted from the dictionary
        index.upsert(
            [(result_id, vector, {"task": task["task_name"], "result": f"{result}\nCommand: {command}\nCommand result: {command_result}"})],
      namespace=OBJECTIVE_PINECONE_COMPAT
        )
        #print(enriched_result)

        # Step 3: Create new tasks and reprioritize task list
        new_tasks = task_creation_agent(
            OBJECTIVE,
            enriched_result,
            task["task_name"],
            tasks_storage.get_task_names(),
        )

        for new_task in new_tasks:
            new_task.update({"task_id": tasks_storage.next_task_id()})
            tasks_storage.append(new_task)

        prioritization_agent()

    time.sleep(5)  # Sleep before checking the task list again
