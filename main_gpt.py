import os
import json
import sys
import venv
import datetime
from dotenv import load_dotenv
import asyncio
import signal

import litellm
from typing import Tuple, Optional
from gpt_functions import functions, CREATE_FILE_FUNC_NAME, CREATE_FOLDER_FUNC_NAME, LIST_FILES_FUNC_NAME, READ_FILE_FUNC_NAME,  UPDATE_FILE_FUNC_NAME, EXECUTE_CODE_FUNC_NAME, STOP_PROCESS_FUNC_NAME, BASE_SYSTEM_PROMPT, AUTOMODE_SYSTEM_PROMPT, CHAIN_OF_THOUGHT_PROMPT

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

# Load environment variables
load_dotenv()
console = Console()

# CONFIG PARAMETERS
AUTO_ITERATION_NUM = 20
AUTOMODE_COMPLETE_PHRASE = "AUTOMODE_COMPLETE"


def setup_virtual_environment() -> Tuple[str, str]:
    venv_name = "code_execution_env"
    venv_path = os.path.join(os.getcwd(), venv_name)
    try:
        if not os.path.exists(venv_path):
            venv.create(venv_path, with_pip=True)
        
        # Activate the virtual environment
        if sys.platform == "win32":
            activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
        else:
            activate_script = os.path.join(venv_path, "bin", "activate")
        
        return venv_path, activate_script
    except Exception as e:
        console.print(f"Error setting up virtual environment: {str(e)}")
        raise


# Define custom tools
def create_file(path: str, content: str)-> str:
    if os.path.exists(path):
        return f"Error: File '{path}' already exists."
    try:
        with open(path, 'w') as f:
            f.write(content)
        print(f"Tool used: create_file - Created file: {path}")
        return f"File '{path}' created successfully."
    except Exception as e:
        return f"Error creating file: {str(e)}"

def create_folder(path: str)-> str:
    if os.path.exists(path):
        return f"Error: Folder '{path}' already exists."
    try:
        os.makedirs(path, exist_ok=True)
        print(f"Tool used: create_folder - Created folder: {path}")
        return f"Folder '{path}' created successfully."
    except Exception as e:
        return f"Error creating folder: {str(e)}"

def list_files(path: str)-> str:
    try:
        files = os.listdir(path)
        print(f"Tool used: list_files - Listed files in folder: {path}")
        return f"Files in folder '{path}': {', '.join(files)}"
    except Exception as e:
        return f"Error listing files: {str(e)}"

def read_file(path: str)-> str:
    try:
        with open(path, 'r') as f:
            content = f.read()
        print(f"Tool used: read_file - Read file: {path}")
        return f"Content of file '{path}':\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def update_file(name: str, content: str)-> str:
    try:
        with open(name, 'w') as f:
            f.write(content)
        print(f"Tool used: update_file - Updated file: {name}")
        return f"File '{name}' updated successfully."
    except Exception as e:
        return f"Error updating file: {str(e)}"

async def execute_code(code, running_processes = {}, timeout=10):
    venv_path, activate_script = setup_virtual_environment()
    
    # Generate a unique identifier for this process
    process_id = f"process_{len(running_processes)}"
    
    # Write the code to a temporary file
    with open(f"{process_id}.py", "w") as f:
        f.write(code)
    
    # Prepare the command to run the code
    if sys.platform == "win32":
        command = f'"{activate_script}" && python3 {process_id}.py'
    else:
        command = f'source "{activate_script}" && python3 {process_id}.py'
    
    # Create a process to run the command
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        shell=True,
        preexec_fn=None if sys.platform == "win32" else os.setsid
    )
    
    # Store the process in our global dictionary
    running_processes[process_id] = process
    
    try:
        # Wait for initial output or timeout
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        stdout = stdout.decode()
        stderr = stderr.decode()
        return_code = process.returncode
    except asyncio.TimeoutError:
        # If we timeout, it means the process is still running
        stdout = "Process started and running in the background."
        stderr = ""
        return_code = "Running"
    
    execution_result = f"Process ID: {process_id}\n\nStdout:\n{stdout}\n\nStderr:\n{stderr}\n\nReturn Code: {return_code}"
    return process_id, execution_result, running_processes

def stop_process(process_id, running_processes = {}):
    if process_id in running_processes:
        process = running_processes[process_id]
        if sys.platform == "win32":
            process.terminate()
        else:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        del running_processes[process_id]
        return f"Process {process_id} has been stopped.", running_processes
    else:
        return f"No running process found with ID {process_id}.", running_processes

def update_token_count(usage: dict[str, int], state: dict[str,int]) -> dict[str,int]:
    """
    トークン数を合計に加算し、今回の使用量を表示
    """
    console.print("Input tokens: {}, Output tokens: {}".format(state["input"], state["output"]))
    assert type(state["input"]) is int and type(state["output"]) is int
    assert type(usage["prompt_tokens"]) is int and type(usage["completion_tokens"]) is int
    new_state = {
        "input": state["input"] + usage["prompt_tokens"],
        "output": state["output"] + usage["completion_tokens"]
    }
    console.print("New Token State:{}".format(new_state))
    return new_state
    

# Define available functions for the model

def main():
    print("Welcome to the SWE Agent")
    print("You can ask to anything. Type 'quit' to exit.")

    token_sum_state = {"input": 0, "output": 0}

    while True:
        user_input = console.input("[bold cyan]You:[/bold cyan] ")
        
        if user_input.lower() == 'quit':
            break

        iteration_count = 0
        
        message_history_state = [{"role": "user", "content": user_input}]
        running_processes = {}
        while True:
            iteration_count += 1
            # Call GPT-4o-mini
            system_prompt = BASE_SYSTEM_PROMPT  + "\n\n" + AUTOMODE_SYSTEM_PROMPT + "\n\n" + CHAIN_OF_THOUGHT_PROMPT
            response = litellm.completion(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                ] + message_history_state,
                tools=[{"type": "function", "function": func} for func in functions],
                tool_choice="auto",
                parallel_tool_calls=True,
                drop_params=True
            )
            assistant_message = response.choices[0].message
            if assistant_message.content is not None:
                console.print(Markdown(assistant_message.content))
        
            if iteration_count > AUTO_ITERATION_NUM or \
                type(assistant_message.content) is str and AUTOMODE_COMPLETE_PHRASE in assistant_message.content:
                d = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open("conversation_history_{}.json".format(d), "w") as f:
                   f.write(json.dumps(message_history_state, indent=4, default = lambda x: x.__dict__))
                break
            token_sum_state = update_token_count(response.usage, token_sum_state)
            
            
            message_history_state.append(assistant_message)
            # Check if the model wants to call a function
            if assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the appropriate function
                    if function_name == CREATE_FILE_FUNC_NAME:
                        result = create_file(function_args["name"], function_args["content"])
                    elif function_name == CREATE_FOLDER_FUNC_NAME:
                        result = create_folder(function_args["path"])
                    elif function_name == LIST_FILES_FUNC_NAME:
                        result = list_files(function_args["path"])
                    elif function_name == READ_FILE_FUNC_NAME:
                        result = read_file(function_args["path"])
                    elif function_name == UPDATE_FILE_FUNC_NAME:
                        result = update_file(function_args["path"], function_args["content"])
                    elif function_name == EXECUTE_CODE_FUNC_NAME:
                        process_id, result, running_processes = asyncio.run(execute_code(function_args["code"], running_processes))
                        if process_id in running_processes:
                            result += "\n\nNote: The process is still running in the background."
                    elif function_name == STOP_PROCESS_FUNC_NAME:
                        result, running_processes = stop_process(function_args["process_id"], running_processes)
                    else:
                        result = "Unknown function called."
                        console.print(Panel(Markdown(f"## Unknown function called: {function_name}"), title="Error", style="red"))

                    # Send the function result back to the model
                    message_history_state.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": result
                    })

if __name__ == "__main__":
    main()


