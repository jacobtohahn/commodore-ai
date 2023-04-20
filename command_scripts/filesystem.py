import os
from pdfminer.high_level import extract_text
from workspace import path_in_workspace, WORKSPACE_PATH
from typing import List, Union
import fnmatch
import shutil

# Ensure lower_snake_case filenames
def format_filename(filename):
    """Format a filename to be lowercase with underscores"""
    # Split the file path into directory and file name components
    directory, file_name = os.path.split(filename)
    
    # Replace any spaces in the file name with underscores
    file_name = file_name.replace(' ', '_')
    
    # Convert the file name to lowercase
    formatted_filename = file_name.lower()
    
    # # Rejoin the directory and file name components to create the full path
    # formatted_filename = os.path.join(directory, file_name)
    
    return formatted_filename

def is_pdf(file_path):
    with open(file_path, 'rb') as file:
        file_header = file.read(5)
    return file_header == b'%PDF-'

def list_files(path: str = WORKSPACE_PATH, level: int = 0) -> str:
    """
    Generate a human-readable one-line JSON-like representation of a filesystem, starting from the given path.

    Args:
        path (str, optional): The starting path of the filesystem representation.
        Defaults to WORKSPACE_PATH.
        level (int, optional): The current level of indentation. Defaults to 0.

    Returns:
        str: The filesystem representation as a formatted string.
    """
    if not os.path.exists(path):
        return ""

    representation = ""
    entries = sorted(os.listdir(path))
    file_prefix = "file: "
    dir_prefix = "dir: "

    for entry in entries:
        entry_path = os.path.join(path, entry)
        if os.path.isfile(entry_path):
            representation += file_prefix + entry.replace(' ', '_') + ", "
        elif os.path.isdir(entry_path):
            if len(entries) > 0:
                representation += dir_prefix + entry.replace(' ', '_') + " {"
                representation += list_files(entry_path, level + 1)
                representation += "}, "

    return representation.strip().rstrip(',')

def find_file(filename: str, path: str = WORKSPACE_PATH) -> str:
    """Recursively search for a file with the given filename in the filesystem.

    Args:
        filename (str): The name of the file to search for.
        path (str, optional): The path to start the search from. Defaults to WORKSPACE_PATH.

    Returns:
        str: The path to the found file or an empty string if the file is not found.
    """
    for root, dirs, files in os.walk(path):
        if filename in files:
            return os.path.join(root, filename)

    return ""

def find_files(path: str = WORKSPACE_PATH, pattern: str = None) -> List[str]:
    matched_files = []
    if not pattern:
        use_pattern = False
    for root, _, files in os.walk(path):
        for filename in files:
            if not use_pattern:
                pattern = filename
            if fnmatch.fnmatch(filename, pattern):
                matched_files.append(os.path.relpath(os.path.join(root, filename), WORKSPACE_PATH))
    return matched_files

def read_file(filename: str) -> str:
    """Read a file and return the contents

    Args:
        filename (str): The name of the file to read

    Returns:
        str: The contents of the file
    """
    try:
        formatted_filename = format_filename(filename)
        filepath = path_in_workspace(formatted_filename)
        # Check if the file is a PDF and extract text if so
        if is_pdf(filepath):
            text = extract_text(filepath)
            if not text:
                return "COMMAND_ERROR: Could not extract text from PDF"
            else:
                return text
        else:
            with open(filepath, "r", encoding='utf-8') as f:
                content = f.read()
            return content
    except Exception as e:
        return handle_file_error("read", filename, str(e))

def write_file(filename: str, text: str) -> str:
    """Write text to a file

    Args:
        filename (str): The name of the file to write to
        text (str): The text to write to the file

    Returns:
        str: A message indicating success or failure
    """
    try:
        formatted_filename = format_filename(filename)
        filepath = path_in_workspace(formatted_filename)
        existing_filepath = find_file(formatted_filename)

        if existing_filepath and (filepath != path_in_workspace(existing_filepath)):
            print(filepath)
            return f"COMMAND_ERROR: A file with that name already exists in a different location: {existing_filepath}. Use append_to_file instead."
        else:
            directory = os.path.dirname(filepath)
            if not os.path.exists(directory):
                os.makedirs(directory)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        return f"File {filename} written to successfully. Your current files are now: {list_files(WORKSPACE_PATH)}"
    except Exception as e:
        return handle_file_error("write", filename, str(e))
    
def append_file(filename: str, text: str) -> str:
    """Append text to a file

    Args:
        filename (str): The name of the file to append to
        text (str): The text to append to the file

    Returns:
        str: A message indicating success or failure
    """
    try:
        formatted_filename = format_filename(filename)
        filepath = path_in_workspace(formatted_filename)
        existing_filepath = find_file(formatted_filename)

        if existing_filepath and (filepath != path_in_workspace(existing_filepath)):
            return f"COMMAND_ERROR: A file with that name already exists in a different location: {existing_filepath}"
        else:
            directory = os.path.dirname(filepath)
            if not os.path.exists(directory):
                os.makedirs(directory)

        with open(filepath, "a") as f:
            f.write(text)

        return f"Text appended to {filename} successfully. Your current files are now: {list_files(WORKSPACE_PATH)}"
    except Exception as e:
        return handle_file_error("append", filename, str(e))

def delete_file(filename: Union[str, List]) -> str:
    try:
        if isinstance(filename, str):
            filename = [filename]
        files_deleted = []
        errors = []
        for file in filename:
            formatted_filename = format_filename(file)
            found_filepaths = find_files(formatted_filename)
            if not found_filepaths:
                errors.append(f"Error: File {file} not found.")
                continue
            for found_filepath in found_filepaths:
                os.remove(found_filepath)
                files_deleted.append(os.path.basename(found_filepath))

        if errors:
            response = f"COMMAND_ERROR: Errors encountered:\n" + "\n".join(errors)
        response += f"\nFiles {files_deleted} deleted successfully. Your current files are now: {list_files(WORKSPACE_PATH)}"
        return response
    except Exception as e:
        return handle_file_error("delete", filename, str(e))
    
def create_directory(directory: Union[str, List]):
    try:
        if isinstance(directory, str):
            directory = [directory]
        directories_created = []
        for dir in directory:
            dir = format_filename(dir)
            dir_path = path_in_workspace(dir)
            os.makedirs(dir_path, exist_ok=True)
            directories_created.append(os.path.basename(dir))
        return f"Directories '{directories_created}' created successfully. Your current files are now: {list_files(WORKSPACE_PATH)}"
    except Exception as e:
        return handle_file_error("create", directory, str(e))
    
def remove_directory(directory: Union[str, List]):
    try:
        if isinstance(directory, str):
            directory = [directory]
        directories_removed = []
        errors = []
        for dir in directory:
            dir = format_filename(dir)
            dir_path = path_in_workspace(dir)
            if not os.path.isdir(dir_path):
                errors.append(dir)
            os.removedirs(dir_path)
            directories_removed.append(os.path.basename(dir))
        if errors:
            response = f"COMMAND_ERROR: Errors encountered:\n" + "\n".join(errors)
        response += f"\nDirectories '{directories_removed}' removed successfully. Your current files are now: {list_files(WORKSPACE_PATH)}"
        return response
    except Exception as e:
        return handle_file_error("remove", directory, str(e))
    
def move_directory(src_directory: Union[str, List], dest_directory: str):
    try:
        if isinstance(src_directory, str):
            src_directory = [src_directory]

            dirs_moved = []
            errors = []

            for dir in src_directory:
                dir = format_filename(dir)
                src_path = path_in_workspace(dir)
                dest_path = path_in_workspace(dest_directory)
                if not os.path.isdir(src_path):
                    errors.append(dir)
                shutil.move(src_path, dest_path)
                dirs_moved.append(os.path.basename(dir))
            if errors:
                response = f"COMMAND_ERROR: Errors encountered:\n" + "\n".join(errors)
            response += f"Directories '{dirs_moved}' moved successfully. Your current files are now: {list_files(WORKSPACE_PATH)}"
            return response
    except Exception as e:
        return handle_file_error("move", src_directory, str(e))

def handle_file_error(operation: str, filename: str, error: str) -> str:
    """
    Handle file-related errors by printing a message with the current filesystem and the error.

    Args:
        operation (str): The operation being performed on the file.
        filename (str): The filename involved in the error.
        error (str): The error message.

    Returns:
        str: The full error message containing the operation, filename, error, and current filesystem.
    """
    current_filesystem = list_files(WORKSPACE_PATH)
    error_message = f"COMMAND_ERROR: Error trying to {operation} {filename} - File likely doesn't exist. Current filesystem:\n{current_filesystem}\nError: {error}"
    print(error_message)
    return error_message