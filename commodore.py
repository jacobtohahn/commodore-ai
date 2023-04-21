"""Main Commodore script"""
import os
import re
import time
from collections import deque
from typing import Dict, List
from dotenv import load_dotenv
import openai
import pinecone
from constraints_capabilities import capabilities_generator
from command_scripts.commands import commands_generator, prepare_commands_list
from command_scripts.execute_command import execute_command

# Class for text colors
class BColors:
    """Terminal text stying"""
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
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0"))

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
print(f"{BColors.OKGREEN}{BColors.BOLD}\nWELCOME TO COMMODORE!\n{BColors.ENDC}")

# Check if we know what we are doing
assert OBJECTIVE, "OBJECTIVE environment variable is missing from .env. Cannot proceed."
assert INITIAL_TASK, "INITIAL_TASK environment variable is missing from .env. Cannot proceed."

# Print the AI configuration:
print(f"{BColors.OKCYAN}Current AI configuration:{BColors.ENDC}")
print(f"{COMMODORE_NAME} is an AI based on {OPENAI_API_MODEL} designed to {OBJECTIVE}.\n"
      f"To do this, it will first start by performing the following task:")

# Configure OpenAI and Pinecone
openai.api_key = OPENAI_API_KEY
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

# Create Pinecone index
TABLE_NAME = "commodore-ai"
DIMENSION = 1536
METRIC = "cosine"
POD_TYPE = "p1"
if TABLE_NAME not in pinecone.list_indexes():
    pinecone.create_index(
        TABLE_NAME, dimension=DIMENSION, metric=METRIC, pod_type=POD_TYPE
    )

# Connect to the index
index = pinecone.Index(TABLE_NAME)

# Clear previous memories
index.delete(delete_all=True, namespace=OBJECTIVE_PINECONE_COMPAT)

class SingleTaskListStorage:
    """Task storage supporting only a single instance of Commodore"""
    def __init__(self):
        self.tasks = deque([])
        self.task_id_counter = 0

    def append(self, task_to_append: Dict):
        """Append a task to the task storage"""
        self.tasks.append(task_to_append)

    def replace(self, tasks: List[Dict]):
        """Replace tasks with a new list of tasks"""
        self.tasks = deque(tasks)

    def popleft(self):
        """Remove the latest task from the task list"""
        return self.tasks.popleft()

    def read_current(self):
        """Read the latest task"""
        return self.tasks[0]

    def is_empty(self):
        """Check if the task list is empty"""
        return False if self.tasks else True

    def next_task_id(self):
        """Get the next task ID"""
        self.task_id_counter += 1
        return self.task_id_counter

    def get_task_names(self):
        """Get the names of the tasks in the task list"""
        return [t["task_name"] for t in self.tasks]

# Initialize tasks storage
tasks_storage = SingleTaskListStorage()

def get_ada_embedding(text):
    """Get embedding for the input text"""
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")[
        "data"
    ][0]["embedding"]

def openai_call(
    prompt: str,
    model: str = OPENAI_API_MODEL,
    temperature: float = OPENAI_TEMPERATURE,
    max_tokens: int = 100,
):
    """Interface with the OpenAI API"""
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
        # except openai.error.InvalidRequestError:
        #     print(
        #         "   *** OpenAI API invalid request. Check the documentation for the specific API method you are calling and make sure you are sending valid and complete parameters. Waiting 10 seconds and trying again. ***"
        #     )
        #     time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.ServiceUnavailableError:
            print(
                "   *** OpenAI API service unavailable. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        else:
            break

# Define the execution agent
def execution_agent(
        objective: str,
        input_task: str,
        context: str,
        failed_result: str = None,
        last_error: str = None
        ) -> str:
    """
    Executes a task based on the given objective and previous context.

    Args:
        objective (str): The objective or goal for the AI to perform the task.
        task (str): The task to be executed by the AI.

    Returns:
        str: The response generated by the AI for the given task.
    """
    prompt = f"""
    You are an AI that is part of an overall AI system who is given a task based on the following objective: {objective}.
    Using the task, generate an output action that obeys the given constraints, capabilities, commands, and previous tasks.
    If the task contains a website URL or article, your action should involve browsing the internet.
    Always include the full URL to any website you mention.
    Only use valid URLs which were given by a previous Google search.
    Take into account these previously completed tasks and context: {context}.
    Use the commands available to the system to guide your response: {commands_generator.commands}.
    Task to translate: {input_task}.
    Your response must be within to the following constraints and capabilities:
    {constraints_capabilities}.
    Only one action should be performed. Do not use the word "and" in your response.
    Your response should be heavily based off of the given task.
    """
    if failed_result and last_error:
        prompt += f"The last time you generated a response, it was used to create a command which returned an error: {last_error}.\n"
        prompt += f"Your last generated response was: {failed_result}.\n"
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

def keyword_agent(input_prompt: str):
    """
    Generates relevant keywords based on an input string.
    """
    prompt = f"""
    You are an AI who generates relevant keywords based on an action being performed by an input prompt.
    Understand the overall single task of the input prompt and generate keywords based on it. 
    If there are multiple actions performed in the input, only focus on the first action and ignore the rest.
    When generating your keywords, ensure they are related to these commands: {commands_generator.commands}.
    "Read article" refers to browsing the internet.
    Your prompt: {input_prompt}
    Format your response as an array of individual keywords. Only include one word per array index.
    Response:"""
    return openai_call(prompt.replace("\n", " "), max_tokens=2000)

def command_translation_agent(command_prompt: str, keywords_list: str, previous_command_result: str) -> str:
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
"Search the internet" refers to the "google" command.
If the task to translate includes a website URL, use the "browse_website" command. "Read article" refers to an google search or webpage browse while "Read file" refers to a filesystem command.
Always use the full url, including any subpages.
If the task contains multiple steps, only translate the first step of the task.
The task to translate into the response format is: {command_prompt}.
Use these keywords to help you choose a command: {keywords_list}.
The result of the previous command is: {previous_command_result}.
ONLY GENERATE ONE COMMAND.
Response:"""
    return openai_call(prompt.replace("\n", " "), max_tokens=2000)

def task_creation_agent(
    objective: str, last_result: Dict, task_description: str, task_list: List[str], context: str
):
    prompt = f"""
    You are a task creation AI for an overall AI system that uses the result of an execution agent to create new tasks, each performing a single action, with the following objective: {objective},
    Take into account these previously completed tasks and context: {context}.
    The last completed task had the result: {last_result}.
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
    updated_tasks = response.split("\n") if "\n" in response else [response]
    return [{"task_name": task_name} for task_name in updated_tasks]

def prioritization_agent(previous_command_result: str, context: str):
    task_names = tasks_storage.get_task_names()
    next_task_id = tasks_storage.next_task_id()
    prompt = f"""
    You are a task formatting AI for an overall AI system tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}.
    Consider the ultimate objective of your team:{OBJECTIVE}.
    Also consider the result of the last completed command: {previous_command_result}.
    Retain all task specifics and details.
    Do not create new tasks.
    Split tasks with multiple steps into individual tasks with one step per task, unless the tasks are to create and write a file. Those two actions are one step.
    Delete redundant tasks.
    Return the result as a numbered list, like:
    #. First task
    #. Second task
    Always start the task list with number {next_task_id}.
    Do not repeat these previously completed tasks: {context}.
    Response:"""
    response = openai_call(prompt)
    updated_tasks = response.split("\n") if "\n" in response else [response]
    updated_tasks_list = []
    for task_string in updated_tasks:
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            updated_tasks_list.append({"task_id": task_id, "task_name": task_name})
    tasks_storage.replace(updated_tasks_list)

# Add the initial task
initial_task = {
    "task_id": tasks_storage.next_task_id(),
    "task_name": INITIAL_TASK
}
tasks_storage.append(initial_task)

COMMAND_RESULT = ""
while True: # Main loop
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

        COMMAND_LOOP_COUNT = 0
        COMMAND_ERROR = None
        PREVIOUS_RESULT = None
        # Command Loop
        while True:
            if COMMAND_LOOP_COUNT >= 5:
                print(f"{BColors.FAIL}*****TOO MANY COMMAND ERRORS*****{BColors.ENDC}")
                print("Quitting...")
                exit()
            # Send to execution function to complete the task based on the context
            execution_context = context_agent(task["task_name"], top_results_num=5)
            while True:
                try:
                    result = execution_agent(
                        OBJECTIVE, task["task_name"],
                        execution_context, PREVIOUS_RESULT,
                        COMMAND_ERROR
                        )
                    break
                except openai.error.InvalidRequestError:
                    if len(execution_context) > 0:
                        # If we're sending to much data, cut some context
                        print("Prompt too long, cutting context...")
                        execution_context = execution_context[:-1]
                        continue
                except Exception as exc:
                    raise RuntimeError(
                        'Execution agent prompt too long and cannot be truncated.'
                        ) from exc
            print("\033[93m\033[1m" + "\n*****ACTION*****\n" + "\033[0m\033[0m")
            print(result)

            # Generate keywords
            keywords = keyword_agent(result)
            print("\033[93m\033[1m" + "\n*****KEYWORDS*****\n" + "\033[0m\033[0m")
            print(keywords)

            # Step 2: Send natural language result to command translator with keywords
            command = command_translation_agent(result, keywords, COMMAND_RESULT)
            print("\033[93m\033[1m" + "\n*****COMMAND*****\n" + "\033[0m\033[0m")
            print(command)

            # Step 3: Execute command
            LOOP_COUNT = 0
            command_return = execute_command(command)
            while (str(command_return).startswith("COMMAND_ERROR:") | str(command_return).startswith("ERROR:")) and LOOP_COUNT < 3:
                print("Command error, trying to fix...")
                new_command = command_translation_agent(f"""
                The last command you entered, {command},
                which was generated based on the following request: {result},
                did not execute correctly and returned this error: {command_return}
                Ensure you are using the proper command name and arguments.
                Please regenerate the command with the required modifications based on the commands list to fix the error. Do not change the command used, only modify the arguments.
                """, keywords, COMMAND_RESULT)
                command_return = execute_command(new_command)
                command = new_command
                LOOP_COUNT += 1
            if LOOP_COUNT >= 2:
                # At this point it can be assumed something was wrong with the command translation input
                # Best solution is to restart the command loop...
                print(f"{BColors.WARNING}Something went wrong... restarting command loop{BColors.ENDC}")
                COMMAND_ERROR = f"Command {new_command} returned: {command_return}"
                print(COMMAND_ERROR)
                PREVIOUS_RESULT = result
                LOOP_COUNT = 0
                COMMAND_LOOP_COUNT += 1
                time.sleep(1)
                continue
            else:
                COMMAND_RESULT = command_return
                COMMAND_LOOP_COUNT = 0
                break
        print(f"{BColors.OKGREEN}{BColors.BOLD}\n*****COMMAND RESULT*****\n{BColors.ENDC}")
        print(COMMAND_RESULT)

        # Now that we know the task was completed successfully, we can remove it from the list
        tasks_storage.popleft()

        # Step 3: Enrich result and command and store in Pinecone
        ### NOT FINISHED ###
        # Don't store the entire google result in memory, which should hopefully cut context length
        if command == "google":
            enriched_result = {"data": command}
        else:
            enriched_result = {
                "data": str(COMMAND_RESULT)
            }  # This is where you should enrich the result if needed
        result_id = f"result_{task['task_id']}"
        vector = get_ada_embedding(
            enriched_result["data"]
        )  # get vector of the actual result extracted from the dictionary
        index.upsert(
            [(result_id, vector, {"task": task["task_name"], "result": str(COMMAND_RESULT)})],
      namespace=OBJECTIVE_PINECONE_COMPAT
        )

        # Step 3: Create new tasks and reprioritize task list
        task_creation_context = context_agent(query=task["task_name"], top_results_num=5)
        while True:
            try:
                new_tasks = task_creation_agent(
                    OBJECTIVE,
                    enriched_result,
                    task["task_name"],
                    tasks_storage.get_task_names(),
                    task_creation_context
                )
                break
            except openai.error.InvalidRequestError:
                if len(task_creation_context) > 0:
                    # If we're sending to much data, cut some context
                    print("Prompt too long, cutting context...")
                    task_creation_context = task_creation_context[:-1]
                    continue
            except Exception as exc:
                raise RuntimeError(
                    "Task creation agent prompt too long and cannot be truncated."
                    ) from exc
        for new_task in new_tasks:
            new_task.update({"task_id": tasks_storage.next_task_id()})
            tasks_storage.append(new_task)
        prioritization_context = context_agent(query=str(PREVIOUS_RESULT), top_results_num=5)
        while True:
            try:
                prioritization_agent(enriched_result, prioritization_context)
                break
            except openai.error.InvalidRequestError:
                if len(task_creation_context) > 0:
                    # If we're sending to much data, cut some context
                    print("Prompt too long, cutting context...")
                    prioritization_context = prioritization_context[:-1]
                    continue
            except Exception as exc:
                raise RuntimeError(
                    "Task creation agent prompt too long and cannot be truncated."
                    ) from exc

    time.sleep(5)  # Sleep before checking the task list again
