"""React project creation and npm execution tools."""

import os
import re
import subprocess
from agent.events import emit_event

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
