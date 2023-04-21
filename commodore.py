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
COMMODORE_NAME = os.getenv("COMMODORE_NAME", "Commodore")

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
print(f"{bcolors.OKGREEN}{bcolors.BOLD}\nWELCOME TO COMMODORE!\n{bcolors.ENDC}")

# Check if we know what we are doing
assert OBJECTIVE, "OBJECTIVE environment variable is missing from .env. Cannot proceed."
assert INITIAL_TASK, "INITIAL_TASK environment variable is missing from .env. Cannot proceed."

# Print the AI configuration:
print(f"{bcolors.OKCYAN}Current AI configuration:{bcolors.ENDC}")
print(f"{COMMODORE_NAME} is an AI based on {OPENAI_API_MODEL} designed to {OBJECTIVE}.\n"
      f"To do this, it will first start by performing the following task:")

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
    
    def read_current(self):
        return self.tasks[0]

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
def execution_agent(objective: str, task: str, previous_result: str = None, command_error: str = None) -> str:
    """
    Executes a task based on the given objective and previous context.

    Args:
        objective (str): The objective or goal for the AI to perform the task.
        task (str): The task to be executed by the AI.

    Returns:
        str: The response generated by the AI for the given task.
    """
    
    context = context_agent(query=task, top_results_num=5)
    prompt = f"""
    You are an AI that is part of an overall AI system who is given a task based on the following objective: {objective}.
    Using the task, generate an output action that obeys the given constraints, capabilities, commands, and previous tasks.
    If the task contains a website URL or article, your action should involve browsing the internet.
    Take into account these previously completed tasks and context: {context}.
    Use the commands available to the system to guide your response: {commands_generator.commands}.
    Your task: {task}
    Your response must be within to the following constraints and capabilities:
    {constraints_capabilities}
    Only one action should be performed. Do not use the word "and" in your response.
    """
    if previous_result and command_error:
        prompt += f"The last time you generated a response, it was used to create a command which returned an error: {command_error}.\n"
        prompt += f"Your last generated response was: {previous_result}.\n"
        prompt += "Modifiy your response so that it does not generate a command which results in an error.\n"
    prompt += "Response:"
    return openai_call(prompt.replace("\n", " "), max_tokens=2000)

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
    return [(str(item.metadata).replace("\n", " ")) for item in sorted_results]

def keyword_agent(input: str):
    """
    Generates relevant keywords based on an input string.
    """
    context = context_agent(query=input, top_results_num=5)
    prompt = f"""
    You are an AI who generates relevant keywords based on an action being performed by an input prompt.
    Understand the overall single task of the input prompt and generate keywords based on it. 
    If there are multiple actions performed in the input, only focus on the first action and ignore the rest.
    When generating your keywords, ensure they are related to these commands: {commands_generator.commands}.
    Take into account these previously completed tasks and context: {context}.
    "Read article" refers to browsing the internet.
    Your prompt: {input}
    Format your response as an array of individual keywords. Only include one word per array index.
    Response:"""
    return openai_call(prompt.replace("\n", " "), max_tokens=2000)

def command_translation_agent(command_prompt: str, keywords: str) -> str:
    context = context_agent(query=command_prompt, top_results_num=5)
    prompt = f"""You are an AI responsible for translating a task into a single command of a specified output format.
Your output format, which you must exactly adhere to at all times, is as follows:
{commands_generator.command_format}
Do not omit any piece of this response format or add any text other than the response format. Fill in the placeholder values with the actual command you want to use.
The response should be all on one line.
These are your available commands:
{commands_generator.commands}.
Your response must adhere exactly to the following constraints and capabilities: {constraints_capabilities}
You MUST use a command exclusively from the list provided above.
If the task does not seem to use a command available to you, use the command no_command.
Argument keys must be listed exactly as specified.
Take into account these previously completed tasks and context: {context}.
"Search the internet" refers to the "google" command.
If the task to translate includes a website URL, use the "browse_website" command. "Read article" refers to an google search or webpage browse while "Read file" refers to a filesystem command.
If the task contains multiple steps, only translate the first step of the task.
The task to translate into the response format is: {command_prompt}.
Use these keywords to help you choose a command: {keywords}.
ONLY GENERATE ONE COMMAND.
Response:"""
    return openai_call(prompt.replace("\n", " "), max_tokens=2000)

def task_creation_agent(
    objective: str, result: Dict, task_description: str, task_list: List[str]
):
    context = context_agent(query=task_description, top_results_num=5)
    prompt = f"""
    You are a task creation AI for an overall AI system that uses the result of an execution agent to create new tasks, each performing a single action, with the following objective: {objective},
    Take into account these previously completed tasks and context: {context}.
    The last completed task had the result: {result}.
    This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join(task_list)}.
    Consider the commands available to the system: {commands_generator.commands}.
    Your response must adhere exectly to the following constraints and capabilities: {constraints_capabilities}
    Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete or completed tasks.
    Include specifics and full URLs in your response if applicable. Be detailed.
    If you reference a website, you MUST include the entire URL in your response.
    Return the tasks as an array. 
    Do not perform a task that has already been performed.
    Do not return a command, only a task description. Only perform one unique task per array index."""
    response = openai_call(prompt)
    new_tasks = response.split("\n") if "\n" in response else [response]
    return [{"task_name": task_name} for task_name in new_tasks]

def prioritization_agent(previous_result: str):
    task_names = tasks_storage.get_task_names()
    next_task_id = tasks_storage.next_task_id()
    context = context_agent(query=str(previous_result), top_results_num=5)
    prompt = f"""
    You are a task formatting AI for an overall AI system tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}.
    Consider the ultimate objective of your team:{OBJECTIVE}.
    Also consider the result of the last completed command: {previous_result}.
    Retain all task specifics and details.
    Do not create new tasks.
    Split tasks with multiple steps into individual tasks with one step per task, unless the tasks are to create and write a file. Those two actions are one step.
    Delete redundant tasks.
    Return the result as a numbered list, like:
    #. First task
    #. Second task
    Start the task list with number {next_task_id}.
    Take into account these previously completed tasks and context: {context}.
    Response:"""
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

        # Step 1: Get the first incomplete task
        task = tasks_storage.read_current()
        print("\033[92m\033[1m" + "\n*****NEXT TASK*****\n" + "\033[0m\033[0m")
        print(task['task_name'])
        
        command_loop_count = 0
        command_error = None
        previous_result = None
        # Command Loop
        while True:
            if command_loop_count >= 5:
                print(f"{bcolors.FAIL}*****TOO MANY COMMAND ERRORS*****{bcolors.ENDC}")
                print("Quitting...")
                exit()
            # Send to execution function to complete the task based on the context
            result = execution_agent(OBJECTIVE, task["task_name"], previous_result, command_error)
            print("\033[93m\033[1m" + "\n*****ACTION*****\n" + "\033[0m\033[0m")
            print(result)

            # Generate keywords
            keywords = keyword_agent(result)
            print("\033[93m\033[1m" + "\n*****KEYWORDS*****\n" + "\033[0m\033[0m")
            print(keywords)

            # Step 2: Send natural language result to command translator with keywords
            command = command_translation_agent(result, keywords)
            print("\033[93m\033[1m" + "\n*****COMMAND*****\n" + "\033[0m\033[0m")
            print(command)

            # Step 3: Execute command
            loop_count = 0
            command_return = execute_command(command)
            while (str(command_return).startswith("COMMAND_ERROR:") | str(command_return).startswith("ERROR:")) and loop_count < 3:
                new_command = command_translation_agent(f"""
                The last command you entered, {command},
                which was generated based on the following request: {result},
                did not execute correctly and returned this error: {command_return}
                Please regenerate the command with the required modifications based on the commands list to fix the error.
                """, keywords)
                command_return = execute_command(new_command)
                loop_count += 1
            if loop_count >= 2:
                # At this point it can be assumed something was wrong with the command translation input
                # Best solution is to restart the command loop...
                print(f"{bcolors.WARNING}Something went wrong... restarting command loop{bcolors.ENDC}")
                command_error = f"Command {new_command} returned: {command_return}"
                print(command_error)
                previous_result = result
                loop_count = 0
                command_loop_count += 1
                time.sleep(1)
                continue
            else:
                command_result = command_return
                command_loop_count = 0
                break
        print(f"{bcolors.OKGREEN}{bcolors.BOLD}\n*****COMMAND RESULT*****\n{bcolors.ENDC}")
        print(command_result)

        # Now that we know the task was completed successfully, we can remove it from the list
        tasks_storage.popleft()

        # Step 3: Enrich result and command and store in Pinecone
        ### NOT FINISHED ###
        enriched_result = {
            "data": str(command_result)
        }  # This is where you should enrich the result if needed
        result_id = f"result_{task['task_id']}"
        vector = get_ada_embedding(
            enriched_result["data"]
        )  # get vector of the actual result extracted from the dictionary
        index.upsert(
            [(result_id, vector, {"task": task["task_name"], "result": str(command_result)})],
      namespace=OBJECTIVE_PINECONE_COMPAT
        )

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

        prioritization_agent(enriched_result)

    time.sleep(5)  # Sleep before checking the task list again
