# flake8: noqa

from dotenv import load_dotenv
from google import genai  # pip install google-genai
import json
import subprocess
import os
import sys
import re
from pathlib import Path


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

# Initialize Gemini client
client = genai.Client()


# ============================================================
# FILE SYSTEM TOOLS
# ============================================================

def write_file(file_path: str, content: str):
    """
    Write content to a file. Creates directories if needed.
    
    Parameters:
    - file_path: The path where the file should be created
    - content: The content to write to the file
    """
    try:
        # Create parent directories if they don't exist
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "file_path": file_path,
            "message": f"File created successfully: {file_path}"
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }


def read_file(file_path: str):
    """
    Read content from a file.
    
    Parameters:
    - file_path: The path of the file to read
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "content": content,
            "file_path": file_path
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"File not found: {file_path}"
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }


def list_directory(directory_path: str):
    """
    List contents of a directory.
    
    Parameters:
    - directory_path: The path of the directory to list
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory_path}"
            }
        
        items = []
        for item in path.iterdir():
            items.append({
                "name": item.name,
                "is_directory": item.is_dir(),
                "path": str(item)
            })
        
        return {
            "success": True,
            "items": items,
            "directory": directory_path
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }


def create_react_project(
    bundler: str,
    project_name: str
):
    # In this specific statement, """ """ is used to create a Docstring (Documentation String).
    """
    Prepare the command required to create a React project.
    This tool only prepares the command. It does not execute it.
    
    Parameters:
    - bundler: The bundler to use ('vite' or 'webpack')
    - project_name: The name of the project
    """

    bundler = bundler.lower().strip()
    project_name = project_name.strip()

    if not project_name:
        return {
            "success": False,
            "error": "Project name cannot be empty."
        }

    # Validate project name
    if not re.match(r'^[a-z0-9\-_]+$', project_name):
        return {
            "success": False,
            "error": "Project name must contain only lowercase letters, numbers, hyphens, and underscores."
        }

    # VITE
    if bundler == "vite":
        command = [
            "npm",
            "exec",
            "--yes",
            "create-vite@latest",
            project_name,
            "--",
            "--template",
            "react"
        ]

    # WEBPACK
    elif bundler == "webpack":
        command = [
            "npx",
            "--yes",
            "create-react-app",
            project_name
        ]

    else:
        return {
            "success": False,
            "error": (
                f"Unsupported bundler: {bundler}. "
                "V3 supports Vite and Webpack."
            )
        }

    return {
        "success": True,
        "command": command,
        "project_name": project_name,
        "bundler": bundler,
        "project_path": os.path.join(os.getcwd(), project_name) #getcwd, get Current Working Directory
    }


def run_command(command: list[str], cwd: str = None):
    """
    Execute a command on the local machine.
    
    Parameters:
    - command: The command to execute as a list of strings
    - cwd: The working directory to execute the command in (optional)
    """
    # Windows: npm -> npm.cmd, npx -> npx.cmd
    # UTF-8 decoding is explicitly configured.

    # Validate command
    if not isinstance(command, list): #isinstance, type checking
        return {
            "success": False,
            "error": "Command must be a list."
        }

    if len(command) == 0:
        return {
            "success": False,
            "error": "Command cannot be empty."
        }

    # Make a copy
    command = command.copy()

    # Windows npm / npx compatibility
    if os.name == "nt":
        # "nt" stands for New Technology
        # If it returns "nt", the computer is running Windows.If it returns "posix", the computer is running Mac or Linux.
        if command[0] == "npm":
            command[0] = "npm.cmd"
        elif command[0] == "npx":
            command[0] = "npx.cmd"

    # Execute command
    try:
        print(f"\n⚙️ Executing: {' '.join(command)}")
        if cwd:
            print(f"   Directory: {cwd}")

        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            shell=False
        )

        output_lines = []
        if process.stdout is not None:
            for line in process.stdout:
                line = line.rstrip("\r\n")
                print(f"   {line}")
                output_lines.append(line)

        return_code = process.wait()
        output = "\n".join(output_lines)

        return {
            "success": return_code == 0, # In operating systems, an exit code of 0 means perfection. 
            "exit_code": return_code,
            "output": output
        }

    except FileNotFoundError:
        return {
            "success": False,
            "error": (
                f"Command not found: {command[0]}. "
                "Make sure Node.js and npm are installed."
            )
        }
    except UnicodeDecodeError as error:
        return {
            "success": False,
            "error": f"Unicode decoding error: {str(error)}"
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }


def install_dependencies(project_path: str):
    """
    Install npm dependencies in the project directory.
    
    Parameters:
    - project_path: The path to the project directory
    """
    try:
        if not os.path.exists(project_path):
            return {
                "success": False,
                "error": f"Project directory not found: {project_path}"
            }

        command = ["npm", "install"]
        
        # Windows compatibility
        if os.name == "nt":
            command[0] = "npm.cmd"

        print(f"\n📦 Installing dependencies in: {project_path}")
        print(f"⚙️ Executing: {' '.join(command)}\n")

        # subprocess.Popen: Spawns a new background process on your computer. Unlike subprocess.run(), Popen does not wait for the command to finish; it streams data while the command runs.
        
        process = subprocess.Popen(
            command,
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            shell=False
        )

        output_lines = []
        if process.stdout is not None:
            for line in process.stdout:
                line = line.rstrip("\r\n")
                print(f"   {line}")
                output_lines.append(line)

        return_code = process.wait()
        output = "\n".join(output_lines)

        return {
            "success": return_code == 0,
            "exit_code": return_code,
            "output": output
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }


def install_package(project_path: str, package: str = None):
    """
    Install additional npm packages in the project directory.
    
    Parameters:
    - project_path: The path to the project directory
    - package: The package to install (optional, defaults to none)
    """
    try:
        if not os.path.exists(project_path):
            return {
                "success": False,
                "error": f"Project directory not found: {project_path}"
            }

        command = ["npm", "install"]
        if package:
            command.append(package)
        
        # Windows compatibility
        if os.name == "nt":
            command[0] = "npm.cmd"

        print(f"\n📦 Installing package in: {project_path}")
        print(f"⚙️ Executing: {' '.join(command)}\n")

        process = subprocess.Popen(
            command,
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            shell=False
        )

        output_lines = []
        if process.stdout is not None:
            for line in process.stdout:
                line = line.rstrip("\r\n")
                print(f"   {line}")
                output_lines.append(line)

        return_code = process.wait()
        output = "\n".join(output_lines)

        return {
            "success": return_code == 0,
            "exit_code": return_code,
            "output": output
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }


# ============================================================
# AVAILABLE TOOLS
# ============================================================

available_tools = {
    "create_react_project": create_react_project,
    "run_command": run_command,
    "write_file": write_file,
    "read_file": read_file,
    "list_directory": list_directory,
    "install_dependencies": install_dependencies,
    "install_package": install_package
}


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are a React Application Creation Agent - V3 (Gemini 3.1 Flash Lite).

Your job is to create FULLY FUNCTIONAL React applications based on
the user's requirements. You can create ANY type of React application.

==================================================
CRITICAL WORKFLOW - MUST FOLLOW THIS SEQUENCE
==================================================

STEP 1: create_react_project
  - This prepares the command but does NOT execute it
  - Returns a command array and project_path

STEP 2: run_command
  - Execute the command returned from create_react_project
  - This actually creates the project folder

STEP 3: install_dependencies
  - After project is created, install dependencies
  - Use the project_path from STEP 1

STEP 4: write_file
  - Write all application source files
  - Use 'file_path' and 'content' parameters

STEP 5: Output success

==================================================
EXAMPLE WORKFLOW - WEATHER APP
==================================================

Action 1:
{
    "step": "action",
    "content": "Preparing project creation",
    "function": "create_react_project",
    "input": {"bundler": "vite", "project_name": "weather-app"}
}

Observation 1:
{
    "success": true,
    "command": ["npm", "exec", "--yes", "create-vite@latest", "weather-app", "--", "--template", "react"],
    "project_path": "/path/to/weather-app"
}

Action 2:
{
    "step": "action",
    "content": "Executing project creation",
    "function": "run_command",
    "input": {"command": ["npm", "exec", "--yes", "create-vite@latest", "weather-app", "--", "--template", "react"]}
}

Observation 2:
{
    "success": true,
    "exit_code": 0
}

Action 3:
{
    "step": "action",
    "content": "Installing dependencies",
    "function": "install_dependencies",
    "input": {"project_path": "/path/to/weather-app"}
}

Observation 3:
{
    "success": true,
    "exit_code": 0
}

Action 4:
{
    "step": "action",
    "content": "Creating App.jsx",
    "function": "write_file",
    "input": {"file_path": "weather-app/src/App.jsx", "content": "// React code here"}
}

==================================================
TOOL PARAMETERS (MUST USE EXACT NAMES)
==================================================

1. create_react_project:
   {"bundler": "vite", "project_name": "my-app"}

2. run_command:
   {"command": ["npm", "exec", "--yes", "create-vite@latest", "my-app", "--", "--template", "react"]}
   OR
   {"command": ["npm", "start"], "cwd": "/path/to/project"}

3. write_file:
   {"file_path": "src/App.jsx", "content": "// React code here"}

4. read_file:
   {"file_path": "src/App.jsx"}

5. list_directory:
   {"directory_path": "src"}

6. install_dependencies:
   {"project_path": "/path/to/project"}

7. install_package:
   {"project_path": "/path/to/project", "package": "axios"}

==================================================
APPLICATION TYPES
==================================================

Todo Application:
- Add, delete, toggle complete todos
- Filter (all, active, completed)
- Local storage persistence
- Clean UI with proper styling

Weather Application:
- Search for city
- Current weather (temp, conditions, humidity, wind)
- 5-day forecast
- OpenWeatherMap API (use placeholder key)

Budget Calculator:
- Add income/expense entries
- Categorize transactions
- Display total and remaining budget

Tic Tac Toe Game:
- 3x3 grid
- Player X and O turns
- Win detection
- Reset game
- Score tracking

Infinite Scroller App:
- load 20 items with which has dummy data initially
- everytime we reach at the bottom of our view port load more 20 items 
- once we have 100 items show a message that you have reached max limit 


==================================================
OUTPUT FORMAT
==================================================

Always return valid JSON. Do not include any markdown formatting or backticks.

Question:
{"step": "question", "content": "Question for user", "function": null, "input": {}, "project": {}, "files": []}

Plan:
{"step": "plan", "content": "Application plan", "function": null, "input": {}, "project": {}, "files": [...]}

Action:
{"step": "action", "content": "Action description", "function": "tool_name", "input": {...}, "project": {}, "files": []}

Output:
{"step": "output", "content": "Application created successfully", "function": null, "input": {}, "project": {}, "files": [...]}

==================================================
IMPORTANT RULES
==================================================

1. ALWAYS call run_command after create_react_project
2. ALWAYS call install_dependencies after run_command succeeds
3. Use EXACT parameter names (file_path, project_path, etc.)
4. Write COMPLETE, WORKING code in each file
5. NEVER create placeholder code or TODO comments
6. Use React hooks properly (useState, useEffect, etc.)
7. Include error handling in all components
8. Make responsive designs with CSS
9. Ask for missing information (theme, bundler) before creating
10. Return ONLY valid JSON - no markdown, no backticks, no extra text
11. *** RETURN EXACTLY ONE JSON OBJECT PER RESPONSE ***
    - Do NOT return a "plan" and an "action" together.
    - Do NOT chain multiple steps in one reply.
    - Pick ONE step (question OR plan OR action OR output) and return only that.
    - You will receive the tool's observation in the next turn, then decide the next step.
"""


# ============================================================
# GEMINI API HELPER
# ============================================================

def call_gemini(messages, system_prompt):
    """
    Call Gemini 3.1 Flash Lite API with the given messages.
    
    Parameters:
    - messages: List of message objects with 'role' and 'content'
    - system_prompt: The system prompt to use
    
    Returns:
    - The response text from Gemini
    """
    try:
        # Build the full conversation
        full_prompt = f"{system_prompt}\n\n"
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                # Skip system role as we already added it
                continue
            elif role == "user":
                full_prompt += f"User: {content}\n\n"
            elif role == "assistant":
                full_prompt += f"Assistant: {content}\n\n"
        
        # Add final instruction for JSON response
        full_prompt += "Assistant: "
        
        # Call Gemini with the full prompt
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=full_prompt
        )
        
        return response.text
    
    except Exception as error:
        print(f"\n❌ Gemini API Error:\n{error}")
        return None


def clean_json_response(raw_response):
    """
    Clean the raw response from Gemini to extract valid JSON.
    Handles: markdown fences, leading/trailing text, multiple concatenated
    JSON objects (returns only the first valid one).
    """
    if raw_response is None:
        return None

    raw_response = raw_response.strip()

    # Remove markdown code blocks if present
    if raw_response.startswith("```json"):
        raw_response = raw_response[7:]
    elif raw_response.startswith("```"):
        raw_response = raw_response[3:]

    if raw_response.endswith("```"):
        raw_response = raw_response[:-3]

    raw_response = raw_response.strip()

    # Find the first balanced JSON object using brace counting
    start = raw_response.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(raw_response)):
        ch = raw_response[i]

        if escape:
            escape = False
            continue

        if ch == "\\":
            escape = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                # Found the end of the first complete JSON object
                return raw_response[start:i + 1]

    return None

# ============================================================
# AGENT STATE
# ============================================================

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]


# ============================================================
# HELPER
# ============================================================

def add_message(role, content):
    messages.append(
        {
            "role": role,
            "content": content
        }
    )


# ============================================================
# AGENT LOOP
# ============================================================

print("\n" + "="*50)
print("🤖 React Agent - V3 (Gemini 3.1 Flash Lite)")
print("Complete React Application Creator")
print("="*50)
print("\nType 'exit' to quit.\n")

# Get initial user input
user_input = input("You: ")

if user_input.lower().strip() in ["exit", "quit"]:
    print("\n🤖: Goodbye!")
    sys.exit(0)

add_message("user", user_input)

while True:
    # ========================================================
    # GEMINI REQUEST
    # ========================================================

    try:
        # Call Gemini
        raw_response = call_gemini(messages, SYSTEM_PROMPT)
        
        if raw_response is None:
            print("\n❌ Failed to get response from Gemini")
            break
        
        # Clean the response
        cleaned_response = clean_json_response(raw_response)
        
        if cleaned_response is None:
            print("\n❌ No valid JSON found in response")
            print(f"Raw response: {raw_response}")
            break

    except Exception as error:
        print(f"\n❌ Gemini API Error:\n{error}")
        break

    # ========================================================
    # PARSE RESPONSE
    # ========================================================

    try:
        parsed_response = json.loads(cleaned_response)
    except json.JSONDecodeError:
        print("\n❌ Invalid JSON returned by model:")
        print(cleaned_response)
        break

    # ========================================================
    # STORE ASSISTANT RESPONSE
    # ========================================================

    add_message("assistant", cleaned_response)

    # ========================================================
    # READ AGENT RESPONSE
    # ========================================================

    step = parsed_response.get("step")
    content = parsed_response.get("content", "")
    function_name = parsed_response.get("function")
    tool_input = parsed_response.get("input", {})
    project = parsed_response.get("project", {})
    files = parsed_response.get("files", [])

    # ========================================================
    # QUESTION
    # ========================================================

    if step == "question":
        print(f"\n🤖: {content}")
        user_input = input("\nYou: ")

        if user_input.lower().strip() in ["exit", "quit"]:
            print("\n🤖: Goodbye!")
            break

        add_message("user", user_input)
        continue

    # ========================================================
    # PLAN
    # ========================================================

    if step == "plan":
        print(f"\n🧠: {content}")
        if files:
            print("\n📁 Files to create:")
            for file in files:
                print(f"   - {file}")
        continue

    # ========================================================
    # ACTION
    # ========================================================

    if step == "action":
        print(f"\n🛠️: Calling {function_name}")
        print(f"   Input: {json.dumps(tool_input, indent=2)}")

        # Validate tool
        if function_name not in available_tools:
            observation = {
                "success": False,
                "error": f"Unknown tool: {function_name}"
            }
        else:
            tool = available_tools[function_name]
            try:
                observation = tool(**tool_input)
            except TypeError as error:
                observation = {
                    "success": False,
                    "error": f"Invalid tool input: {str(error)}"
                }
            except Exception as error:
                observation = {
                    "success": False,
                    "error": str(error)
                }

        # Display observation
        print("\n🔍 Observation:")
        print(json.dumps(observation, indent=2, ensure_ascii=False))

        # Send observation back to model
        observation_message = {
            "step": "observe",
            "output": observation,
            "project": project,
            "files": files
        }

        add_message("user", json.dumps(observation_message, ensure_ascii=False))
        continue

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    if step == "output":
        print(f"\n✅ {content}")
        
        if project:
            print("\n📦 Project Details:")
            print(json.dumps(project, indent=2, ensure_ascii=False))
        
        if files:
            print(f"\n📁 Created Files ({len(files)}):")
            for file in files:
                print(f"   - {file}")
        
        break

    # ========================================================
    # UNKNOWN STEP
    # ========================================================

    print(f"\n❌ Unknown agent step: {step}")
    print(json.dumps(parsed_response, indent=2, ensure_ascii=False))
    break