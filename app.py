# flake8: noqa

from dotenv import load_dotenv
from google import genai  # pip install google-genai
import json
import subprocess
import os
import sys
import socket
import time
import signal
import re
from pathlib import Path

import urllib.request
import urllib.error

import random


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

# Initialize Gemini client
client = genai.Client()


# ============================================================
# STREAMING CALLBACK
# ============================================================

# Used by the Streamlit UI to receive agent/tool events as they happen.
event_callback = None


def set_event_callback(callback):
    """Set a callback that receives live agent/tool events."""
    global event_callback
    event_callback = callback


def emit_event(event):
    """Send an event to the active UI, if one is connected."""
    if event_callback is not None:
        try:
            event_callback(event)
        except Exception:
            # UI streaming must never break the agent itself.
            pass


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

        emit_event({
            "step": "command_start",
            "command": command,
            "cwd": cwd
        })

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
                emit_event({
                    "step": "command_output",
                    "line": line
                })

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

        emit_event({
            "step": "command_start",
            "command": command,
            "cwd": project_path
        })

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
                emit_event({
                    "step": "command_output",
                    "line": line
                })

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

        emit_event({
            "step": "command_start",
            "command": command,
            "cwd": project_path
        })

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
                emit_event({
                    "step": "command_output",
                    "line": line
                })

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


# deploy_to_cloudflare_pages
def deploy_to_cloudflare_pages(project_path: str, project_name: str):
    """
    Build a React application and deploy its dist folder
    to Cloudflare Pages using Direct Upload.
    """

    try:
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")

        if not account_id or not api_token:
            return {
                "success": False,
                "error": (
                    "Cloudflare credentials are not configured. "
                    "Set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN."
                )
            }

        if not os.path.isdir(project_path):
            return {
                "success": False,
                "error": f"Project directory not found: {project_path}"
            }

        # --------------------------------------------------------
        # STEP 1: Build React application
        # --------------------------------------------------------

        emit_event({
            "step": "deployment_build_starting",
            "project_path": project_path,
            "project_name": project_name
        })

        build_command = ["npm", "run", "build"]

        if os.name == "nt":
            build_command[0] = "npm.cmd"

        build_process = subprocess.Popen(
            build_command,
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

        build_output = []

        if build_process.stdout is not None:
            for line in build_process.stdout:
                line = line.rstrip("\r\n")
                build_output.append(line)

                emit_event({
                    "step": "command_output",
                    "line": line
                })

        build_exit_code = build_process.wait()

        if build_exit_code != 0:
            return {
                "success": False,
                "error": "React production build failed.",
                "exit_code": build_exit_code,
                "output": "\n".join(build_output)
            }

        dist_path = os.path.join(project_path, "dist")

        if not os.path.isdir(dist_path):
            return {
                "success": False,
                "error": f"Build completed but dist directory was not found: {dist_path}"
            }

        # --------------------------------------------------------
        # STEP 2: Check/create Cloudflare Pages project
        # --------------------------------------------------------

        api_base = (
            f"https://api.cloudflare.com/client/v4"
            f"/accounts/{account_id}/pages/projects/{project_name}"
        )

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        project_exists = False

        try:
            request = urllib.request.Request(
                api_base,
                headers=headers,
                method="GET"
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status == 200:
                    project_exists = True

        except urllib.error.HTTPError as error:
            if error.code != 404:
                error_body = error.read().decode("utf-8", errors="replace")

                return {
                    "success": False,
                    "error": (
                        f"Cloudflare project lookup failed: "
                        f"HTTP {error.code} - {error_body}"
                    )
                }

        # --------------------------------------------------------
        # STEP 3: Create Pages project if necessary
        # --------------------------------------------------------

        if not project_exists:
            create_url = (
                f"https://api.cloudflare.com/client/v4"
                f"/accounts/{account_id}/pages/projects"
            )

            payload = json.dumps({
                "name": project_name,
                "production_branch": "main"
            }).encode("utf-8")

            request = urllib.request.Request(
                create_url,
                data=payload,
                headers=headers,
                method="POST"
            )

            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    response_body = json.loads(
                        response.read().decode("utf-8")
                    )

                    if not response_body.get("success"):
                        return {
                            "success": False,
                            "error": (
                                "Cloudflare Pages project creation failed.",
                                response_body
                            )
                        }

            except urllib.error.HTTPError as error:
                error_body = error.read().decode(
                    "utf-8",
                    errors="replace"
                )

                return {
                    "success": False,
                    "error": (
                        f"Cloudflare Pages project creation failed: "
                        f"HTTP {error.code} - {error_body}"
                    )
                }

        # --------------------------------------------------------
        # STEP 4: Deploy dist using Wrangler
        # --------------------------------------------------------

        emit_event({
            "step": "deployment_starting",
            "project_name": project_name
        })

        deploy_command = [
            "npx",
            "wrangler@latest",
            "pages",
            "deploy",
            dist_path,
            "--project-name",
            project_name
        ]

        if os.name == "nt":
            deploy_command[0] = "npx.cmd"

        deploy_env = os.environ.copy()
        deploy_env["CLOUDFLARE_ACCOUNT_ID"] = account_id
        deploy_env["CLOUDFLARE_API_TOKEN"] = api_token

        emit_event({
            "step": "command_start",
            "command": deploy_command,
            "cwd": project_path
        })

        process = subprocess.Popen(
            deploy_command,
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            shell=False,
            env=deploy_env
        )

        output_lines = []

        if process.stdout is not None:
            for line in process.stdout:
                line = line.rstrip("\r\n")
                output_lines.append(line)

                emit_event({
                    "step": "command_output",
                    "line": line
                })

        exit_code = process.wait()

        if exit_code != 0:
            return {
                "success": False,
                "error": "Cloudflare Pages deployment failed.",
                "exit_code": exit_code,
                "output": "\n".join(output_lines)
            }

        # --------------------------------------------------------
        # STEP 5: Return public URL
        # --------------------------------------------------------

        public_url = f"https://{project_name}.pages.dev"

        emit_event({
            "step": "deployment_ready",
            "project_name": project_name,
            "url": public_url
        })

        return {
            "success": True,
            "project_name": project_name,
            "project_path": project_path,
            "dist_path": dist_path,
            "url": public_url,
            "message": "React application deployed successfully to Cloudflare Pages."
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }

# ============================================================
# REACT SERVER TOOLS
# ============================================================

def find_available_port(start_port: int = 5173, max_attempts: int = 100):
    """
    Find an available TCP port.

    The first project normally gets 5173. If that port is already
    occupied, the next available port is used (5174, 5175, ...).
    """
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                sock.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue

    return None


def wait_for_server(port: int, timeout: int = 15):
    """
    Wait until something is responding on localhost:port.
    Returns True when the HTTP server is reachable.
    """

    deadline = time.time() + timeout
    url = f"http://127.0.0.1:{port}"

    while time.time() < deadline:

        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                return response.status < 500

        except urllib.error.HTTPError as error:
            # An HTTP error still proves that the server is alive.
            return error.code < 500

        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            time.sleep(0.25)

    return False


def start_react_app(project_path: str, port: int = 5173):
    """
    Start a Vite React development server in the background.

    If the requested port is occupied, automatically select the
    next available port so multiple projects can run simultaneously.
    """

    try:
        if not os.path.isdir(project_path):
            return {
                "success": False,
                "error": f"Project directory not found: {project_path}"
            }

        requested_port = int(port)

        actual_port = find_available_port(
            start_port=requested_port
        )

        if actual_port is None:
            return {
                "success": False,
                "error": (
                    f"No available port found starting from "
                    f"{requested_port}."
                )
            }

        if actual_port != requested_port:
            emit_event({
                "step": "server_port_changed",
                "requested_port": requested_port,
                "port": actual_port,
                "reason": f"Port {requested_port} is already in use."
            })

        command = [
            "npm",
            "run",
            "dev",
            "--",
            "--host",
            "0.0.0.0",
            "--port",
            str(actual_port),
            "--strictPort"
        ]

        if os.name == "nt":
            command[0] = "npm.cmd"

        log_path = os.path.join(
            project_path,
            ".react-agent-dev.log"
        )

        log_file = open(
            log_path,
            "a",
            encoding="utf-8"
        )

        if os.name == "nt":
            process = subprocess.Popen(
                command,
                cwd=project_path,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                shell=False,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            process = subprocess.Popen(
                command,
                cwd=project_path,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                shell=False,
                start_new_session=True
            )

        log_file.close()

        emit_event({
            "step": "server_starting",
            "project_path": project_path,
            "pid": process.pid,
            "port": actual_port
        })

        # Do not report success until Vite is actually reachable.
        if not wait_for_server(actual_port):
            if process.poll() is not None:
                return {
                    "success": False,
                    "error": (
                        "React server exited before becoming ready. "
                        f"Check {log_path} for details."
                    ),
                    "pid": process.pid,
                    "project_path": project_path,
                    "port": actual_port,
                    "log_file": log_path
                }

            return {
                "success": False,
                "error": (
                    f"React server did not become ready on port "
                    f"{actual_port} within 15 seconds."
                ),
                "pid": process.pid,
                "project_path": project_path,
                "port": actual_port,
                "log_file": log_path
            }

        url = f"http://localhost:{actual_port}"

        emit_event({
            "step": "server_ready",
            "project_path": project_path,
            "pid": process.pid,
            "port": actual_port,
            "url": url
        })

        return {
            "success": True,
            "pid": process.pid,
            "project_path": project_path,
            "port": actual_port,
            "url": url,
            "message": "React development server is ready.",
            "log_file": log_path
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }


def stop_react_app(pid: int):
    """Terminate a React development server by PID."""

    try:
        pid = int(pid)

        if os.name == "nt":
            result = subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            success = result.returncode == 0
            output = result.stdout.strip()

        else:
            os.killpg(pid, signal.SIGTERM)

            # Give the process group a moment to exit cleanly.
            deadline = time.time() + 3

            while time.time() < deadline:
                try:
                    os.killpg(pid, 0)
                    time.sleep(0.1)
                except ProcessLookupError:
                    break

            success = True
            output = f"Process group {pid} terminated."

        emit_event({
            "step": "server_stopped",
            "pid": pid,
            "success": success
        })

        return {
            "success": success,
            "pid": pid,
            "message": (
                "React development server terminated."
                if success
                else "Failed to terminate React development server."
            ),
            "output": output
        }

    except ProcessLookupError:
        return {
            "success": True,
            "pid": pid,
            "message": "React development server was already stopped."
        }

    except Exception as error:
        return {
            "success": False,
            "pid": pid,
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
    "install_package": install_package,
    "deploy_to_cloudflare_pages": deploy_to_cloudflare_pages
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

STEP 5: deploy_to_cloudflare_pages
   - After ALL application files are written
   - Deploy the application to Cloudflare Pages
   - Use the project_path from the project
   - Use the project name as the Cloudflare Pages project name
   - The tool will build the React application
   - The tool will deploy the dist directory
   - The tool will return the public https://<project-name>.pages.dev URL

STEP 6: Output success
   - Return the public Cloudflare Pages URL
   - Do NOT return localhost:5173

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

Action 5:
{
    "step": "action",
    "content": "Deploying React application to Cloudflare Pages",
    "function": "deploy_to_cloudflare_pages",
    "input": {"project_path": "/path/to/weather-app", "project_name": "weather-app"}
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

8. start_react_app:
   {"project_path": "/path/to/project", "port": 5173}

9. stop_react_app:
   {"pid": 12345}

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
3. ALWAYS call deploy_to_cloudflare_pages after all application files have been written
4. The final output must include the public Cloudflare Pages URL
5. NEVER return localhost:5173 as the application URL
6. Write COMPLETE, WORKING code in each file
7. NEVER create placeholder code or TODO comments
8. Use React hooks properly (useState, useEffect, etc.)
9. Include error handling in all components
10. Make responsive designs with CSS
11. Ask for missing information (theme, bundler) before creating
12. Return ONLY valid JSON - no markdown, no backticks, no extra text
13. Production deployment is through deploy_to_cloudflare_pages only.
14. Do NOT call start_react_app or stop_react_app. They are local-development helpers and are not available to the agent.
15. *** RETURN EXACTLY ONE JSON OBJECT PER RESPONSE ***
    - Do NOT return a "plan" and an "action" together.
    - Do NOT chain multiple steps in one reply.
    - Pick ONE step (question OR plan OR action OR output) and return only that.
    - You will receive the tool's observation in the next turn, then decide the next step.
"""


# ============================================================
# GEMINI API HELPER
# ============================================================

PRIMARY_MODEL = "gemini-3.1-flash-lite"
FALLBACK_MODEL = "gemini-3.5-flash-lite"


def call_gemini(messages, system_prompt):
    """
    Call Gemini with retry + fallback handling.

    Retries temporary server/rate-limit errors and falls back
    to another supported model if necessary.
    """

    # Build conversation
    full_prompt = f"{system_prompt}\n\n"

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if role == "system":
            continue
        elif role == "user":
            full_prompt += f"User: {content}\n\n"
        elif role == "assistant":
            full_prompt += f"Assistant: {content}\n\n"

    full_prompt += "Assistant: "

    models_to_try = [
        PRIMARY_MODEL,
        FALLBACK_MODEL,
    ]

    retryable_errors = (
        "503",
        "429",
        "500",
        "502",
        "504",
        "UNAVAILABLE",
        "RESOURCE_EXHAUSTED",
    )

    for model in models_to_try:

        for attempt in range(4):

            try:
                print(
                    f"\n🤖 Gemini request "
                    f"(model={model}, attempt={attempt + 1}/4)"
                )

                response = client.models.generate_content(
                    model=model,
                    contents=full_prompt
                )

                if response.text:
                    return response.text

                raise RuntimeError("Gemini returned an empty response.")

            except Exception as error:

                error_text = str(error)

                print(
                    f"\n❌ Gemini error "
                    f"(model={model}, attempt={attempt + 1}/4):"
                )
                print(error_text)

                # Only retry temporary errors
                if not any(
                    error_code in error_text
                    for error_code in retryable_errors
                ):
                    return None

                # Last attempt for this model
                if attempt == 3:
                    print(
                        f"\n⚠️ {model} failed after 4 attempts."
                    )
                    break

                # Exponential backoff + jitter
                delay = (2 ** attempt) + random.uniform(0, 0.5)

                print(
                    f"⏳ Retrying in {delay:.1f}s..."
                )

                time.sleep(delay)

    print("\n❌ All Gemini models failed.")
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

def create_messages():
    """
    Create a fresh conversation state for an agent session.
    """
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]


# ============================================================
# HELPER
# ============================================================

def add_message(messages, role, content):
    messages.append(
        {
            "role": role,
            "content": content
        }
    )


# ============================================================
# AGENT TURN
# ============================================================

def run_agent_turn(user_input, messages):
    """
    Process one user message through the React agent.

    The agent can perform multiple internal steps:
        user
          ↓
        Gemini
          ↓
        plan / question / action / output
          ↓
        tool execution
          ↓
        observation
          ↓
        Gemini
          ↓
        ...

    Returns:
        {
            "status": "question" | "output" | "error",
            "content": str,
            "project": dict,
            "files": list,
            "events": list
        }
    """

    add_message(messages, "user", user_input)

    events = []

    while True:

        # ====================================================
        # GEMINI REQUEST
        # ====================================================

        try:
            raw_response = call_gemini(messages, SYSTEM_PROMPT)

            if raw_response is None:
                return {
                    "status": "error",
                    "content": (
                        "Gemini is temporarily unavailable. "
                        "The agent retried the request but could not continue."
                    ),
                    "project": {},
                    "files": [],
                    "events": events
                }

            cleaned_response = clean_json_response(raw_response)

            if cleaned_response is None:
                return {
                    "status": "error",
                    "content": "Gemini did not return valid JSON.",
                    "project": {},
                    "files": [],
                    "events": events
                }

        except Exception as error:
            return {
                "status": "error",
                "content": f"Gemini API error: {error}",
                "project": {},
                "files": [],
                "events": events
            }

        # ====================================================
        # PARSE RESPONSE
        # ====================================================

        try:
            parsed_response = json.loads(cleaned_response)

        except json.JSONDecodeError:
            return {
                "status": "error",
                "content": "Invalid JSON returned by Gemini.",
                "project": {},
                "files": [],
                "events": events
            }

        # ====================================================
        # STORE ASSISTANT RESPONSE
        # ====================================================

        add_message(messages, "assistant", cleaned_response)

        # ====================================================
        # READ AGENT RESPONSE
        # ====================================================

        step = parsed_response.get("step")
        content = parsed_response.get("content", "")
        function_name = parsed_response.get("function")
        tool_input = parsed_response.get("input", {})
        project = parsed_response.get("project", {})
        files = parsed_response.get("files", [])

        # Store event for Streamlit UI
        events.append(
            {
                "step": step,
                "content": content,
                "function": function_name,
                "input": tool_input,
                "project": project,
                "files": files
            }
        )

        emit_event({
            "step": step,
            "content": content,
            "function": function_name,
            "input": tool_input,
            "project": project,
            "files": files
        })

        # ====================================================
        # QUESTION
        # ====================================================

        if step == "question":

            return {
                "status": "question",
                "content": content,
                "project": project,
                "files": files,
                "events": events
            }

        # ====================================================
        # PLAN
        # ====================================================

        if step == "plan":

            # No user interaction is required.
            # Continue the agent loop so Gemini can perform
            # the next action.

            continue

        # ====================================================
        # ACTION
        # ====================================================

        if step == "action":

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

            # Store tool observation in events
            events.append(
                {
                    "step": "observation",
                    "content": "",
                    "function": function_name,
                    "input": tool_input,
                    "observation": observation
                }
            )

            emit_event({
                "step": "observation",
                "content": "",
                "function": function_name,
                "input": tool_input,
                "observation": observation
            })

            # =================================================
            # SEND OBSERVATION BACK TO GEMINI
            # =================================================

            observation_message = {
                "step": "observe",
                "output": observation,
                "project": project,
                "files": files
            }

            add_message(
                messages,
                "user",
                json.dumps(
                    observation_message,
                    ensure_ascii=False
                )
            )

            # Continue the agent loop
            continue

        # ====================================================
        # FINAL OUTPUT
        # ====================================================

        if step == "output":

            return {
                "status": "output",
                "content": content,
                "project": project,
                "files": files,
                "events": events
            }

        # ====================================================
        # UNKNOWN STEP
        # ====================================================

        return {
            "status": "error",
            "content": f"Unknown agent step: {step}",
            "project": project,
            "files": files,
            "events": events
        }


# ============================================================
# CLI AGENT
# ============================================================

def run_cli():

    print("\n" + "=" * 50)
    print("🤖 React Agent - V3 (Gemini 3.1 Flash Lite)")
    print("Complete React Application Creator")
    print("=" * 50)

    print("\nType 'exit' to quit.\n")

    messages = create_messages()

    while True:

        user_input = input("You: ")

        if user_input.lower().strip() in ["exit", "quit"]:
            print("\n🤖: Goodbye!")
            break

        result = run_agent_turn(
            user_input,
            messages
        )

        # ====================================================
        # DISPLAY EVENTS
        # ====================================================

        for event in result.get("events", []):

            step = event.get("step")

            if step == "plan":

                print(f"\n🧠: {event.get('content', '')}")

                files = event.get("files", [])

                if files:
                    print("\n📁 Files to create:")

                    for file in files:
                        print(f"   - {file}")

            elif step == "action":

                function_name = event.get("function")
                tool_input = event.get("input", {})

                print(f"\n🛠️: Calling {function_name}")

                print(
                    "   Input: "
                    + json.dumps(
                        tool_input,
                        indent=2,
                        ensure_ascii=False
                    )
                )

            elif step == "observation":

                observation = event.get("observation", {})

                print("\n🔍 Observation:")

                print(
                    json.dumps(
                        observation,
                        indent=2,
                        ensure_ascii=False
                    )
                )

        # ====================================================
        # QUESTION
        # ====================================================

        if result["status"] == "question":

            print(f"\n🤖: {result['content']}")

            continue

        # ====================================================
        # OUTPUT
        # ====================================================

        if result["status"] == "output":

            print(f"\n✅ {result['content']}")

            project = result.get("project", {})
            files = result.get("files", [])

            if project:

                print("\n📦 Project Details:")

                print(
                    json.dumps(
                        project,
                        indent=2,
                        ensure_ascii=False
                    )
                )

            if files:

                print(
                    f"\n📁 Created Files ({len(files)}):"
                )

                for file in files:
                    print(f"   - {file}")

            continue

        # ====================================================
        # ERROR
        # ====================================================

        if result["status"] == "error":

            print(
                f"\n❌ {result['content']}"
            )

            continue


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_cli()