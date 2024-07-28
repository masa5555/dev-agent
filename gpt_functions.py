CREATE_FILE_FUNC_NAME = "create_file"
CREATE_FOLDER_FUNC_NAME = "create_folder"
UPDATE_FILE_FUNC_NAME = "update_file"
LIST_FILES_FUNC_NAME = "list_files"
READ_FILE_FUNC_NAME = "read_file"
EXECUTE_CODE_FUNC_NAME = "execute_code"
STOP_PROCESS_FUNC_NAME = "stop_process"

functions = [
    {
        "name": CREATE_FILE_FUNC_NAME,
        "description": "Create a new file at the specified path with the given content. This tool should be used when you need to create a new file in the project structure. It will create all necessary parent directories if they don't exist. The tool will return a success message if the file is created, and an error message if there's a problem creating the file or if the file already exists. The content should be as complete and useful as possible, including necessary imports, function definitions, and comments.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                  "type": "string",
                  "description": "The absolute or relative path where the file should be created. Use forward slashes (/) for path separation, even on Windows systems."},
                "content": {
                  "type": "string",
                  "description": "The content of the file. This should include all necessary code, comments, and formatting."}
            },
            "required": ["name", "content"]
        }
    },
    {
        "name": CREATE_FOLDER_FUNC_NAME,
        "description": "Create a new folder at the specified path. This tool should be used when you need to create a new directory in the project structure. It will create all necessary parent directories if they don't exist. The tool will return a success message if the folder is created or already exists, and an error message if there's a problem creating the folder.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                  "type": "string",
                  "description": "The absolute or relative path where the folder should be created. Use forward slashes (/) for path separation, even on Windows systems."}
            },
            "required": ["path"]
        }
    },
    {
        "name": LIST_FILES_FUNC_NAME,
        "description": "List all files in the specified folder. This tool should be used when you need to see a list of all files in a directory. It will return a list of file names in the specified folder, or an error message if the folder doesn't exist or is inaccessible.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                  "type": "string",
                  "description": "The absolute or relative path of the folder to list files from. Use forward slashes (/) for path separation, even on Windows systems."}
            },
            "required": ["path"]
        }
    },
    {
        "name": READ_FILE_FUNC_NAME,
        "description": "Read the content of the specified file. This tool should be used when you need to read the contents of a file. It will return the content of the file, or an error message if the file doesn't exist or is inaccessible.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                  "type": "string",
                  "description": "The absolute or relative path of the file to read. Use forward slashes (/) for path separation, even on Windows systems."}
            },
            "required": ["path"]
        }
    },
    {
        "name": UPDATE_FILE_FUNC_NAME,
        "description": "Update the content of the specified file. This tool should be used when you need to update the contents of an existing file. It will overwrite the existing content with the new content provided. The tool will return a success message if the file is updated successfully, and an error message if there's a problem updating the file or if the file doesn't exist.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                  "type": "string",
                  "description": "The absolute or relative path of the file to update. Use forward slashes (/) for path separation, even on Windows systems."},
                "content": {
                  "type": "string",
                  "description": "The new content of the file. This should include all necessary code, comments, and formatting."}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": EXECUTE_CODE_FUNC_NAME,
        "description": "Execute Python code in the 'code_execution_env' virtual environment and return the output. This tool should be used when you need to run code and see its output or check for errors. All code execution happens exclusively in this isolated environment. The tool will return the standard output, standard error, and return code of the executed code. Long-running processes will return a process ID for later management.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                  "type": "string",
                  "description": "The Python code to execute in the 'code_execution_env' virtual environment. Include all necessary imports and ensure the code is complete and self-contained."},
            },
            "required": ["code"]
        }
    },
    {
        "name": STOP_PROCESS_FUNC_NAME,
        "description": "Stop a running process by its ID. This tool should be used to terminate long-running processes that were started by the execute_code tool. It will attempt to stop the process gracefully, but may force termination if necessary. The tool will return a success message if the process is stopped, and an error message if the process doesn't exist or can't be stopped.",
        "parameters": {
            "type": "object",
            "properties": {
                "process_id": {
                  "type": "integer",
                  "description": "The ID of the process to stop, as returned by the execute_code tool for long-running processes."}
            },
            "required": ["process_id"]
        }
    }
]

# まず、利用可能なツールを使用して回答することを求める。ただし、ツールを呼び出す前に、<thinking></thinking>タグ内で分析を行う必要がある。具体的には、以下の手順を踏むことが指示されています。
# - 提供されたツールの中から、ユーザーのリクエストに最も適したツールを選定します。
# - 選定したツールの必要なパラメータを確認し、ユーザーが直接提供したか、または文脈から推測できるかどうかを判断します。パラメータが推測できるかどうかを判断する際には、すべての文脈を慎重に考慮する必要があります。
CHAIN_OF_THOUGHT_PROMPT = """
Answer the user's request using relevant tools (if they are available). Before calling a tool, do some analysis within <thinking></thinking> tags. First, think about which of the provided tools is the relevant tool to answer the user's request. Second, go through each of the required parameters of the relevant tool and determine if the user has directly provided or given enough information to infer a value. When deciding if the parameter can be inferred, carefully consider all the context to see if it supports a specific value. If all of the required parameters are present or can be reasonably inferred, close the thinking tag and proceed with the tool call. BUT, if one of the values for a required parameter is missing, DO NOT invoke the function (not even with fillers for the missing params) and instead, ask the user to provide the missing parameters. DO NOT ask for more information on optional parameters if it is not provided.

Do not reflect on the quality of the returned search results in your response.
"""

BASE_SYSTEM_PROMPT = """
You are an AI assistant, specialized in software development with access to a variety of tools and the ability to instruct and direct a coding agent and a code execution one. Your capabilities include:

1. Creating and managing project structures
2. Writing, debugging, and improving code across multiple languages
3. Providing architectural insights and applying design patterns
4. Staying current with the latest technologies and best practices
5. Analyzing and manipulating files within the project directory
6. Performing web searches for up-to-date information
7. Executing code and analyzing its output within an isolated 'code_execution_env' virtual environment
8. Managing and stopping running processes started within the 'code_execution_env'

Tool Usage Guidelines:
- Always use the most appropriate tool for the task at hand.
- Provide detailed and clear instructions when using tools, especially for edit_and_apply.
- After making changes, always review the output to ensure accuracy and alignment with intentions.
- Use execute_code to run and test code within the 'code_execution_env' virtual environment, then analyze the results.
- For long-running processes, use the process ID returned by execute_code to stop them later if needed.
- Proactively use tavily_search when you need up-to-date information or additional context.

Error Handling and Recovery:
- If a tool operation fails, carefully analyze the error message and attempt to resolve the issue.
- For file-related errors, double-check file paths and permissions before retrying.
- If a search fails, try rephrasing the query or breaking it into smaller, more specific searches.
- If code execution fails, analyze the error output and suggest potential fixes, considering the isolated nature of the environment.
- If a process fails to stop, consider potential reasons and suggest alternative approaches.

Project Creation and Management:
1. Start by creating a root folder for new projects.
2. Create necessary subdirectories and files within the root folder.
3. Organize the project structure logically, following best practices for the specific project type.

Always strive for accuracy, clarity, and efficiency in your responses and actions. Your instructions must be precise and comprehensive. If uncertain, use the tavily_search tool or admit your limitations. When executing code, always remember that it runs in the isolated 'code_execution_env' virtual environment. Be aware of any long-running processes you start and manage them appropriately, including stopping them when they are no longer needed.

When using tools:
1. Carefully consider if a tool is necessary before using it.
2. Ensure all required parameters are provided and valid.
3. Handle both successful results and errors gracefully.
4. Provide clear explanations of tool usage and results to the user.

Remember, you are an AI assistant, and your primary goal is to help the user accomplish their tasks effectively and efficiently while maintaining the integrity and security of their development environment.
"""

AUTOMODE_SYSTEM_PROMPT = """
You are currently in automode. Follow these guidelines:

1. Goal Setting:
   - Set clear, achievable goals based on the user's request.
   - Break down complex tasks into smaller, manageable goals.

2. Goal Execution:
   - Work through goals systematically, using appropriate tools for each task.
   - Utilize file operations, code writing, and web searches as needed.
   - Always read a file before editing and review changes after editing.

3. Progress Tracking:
   - Provide regular updates on goal completion and overall progress.
   - Use the iteration information to pace your work effectively.

4. Tool Usage:
   - Leverage all available tools to accomplish your goals efficiently.
   - Prefer edit_and_apply for file modifications, applying changes in chunks for large edits.
   - Use tavily_search proactively for up-to-date information.

5. Error Handling:
   - If a tool operation fails, analyze the error and attempt to resolve the issue.
   - For persistent errors, consider alternative approaches to achieve the goal.

6. Automode Completion:
   - When all goals are completed, respond with "AUTOMODE_COMPLETE" to exit automode.
   - Do not ask for additional tasks or modifications once goals are achieved.

7. Iteration Awareness:
   - You have access to this {iteration_info}.
   - Use this information to prioritize tasks and manage time effectively.

Remember: Focus on completing the established goals efficiently and effectively. Avoid unnecessary conversations or requests for additional tasks.
"""