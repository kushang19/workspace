"""Local React development server helpers.

These tools are retained for local development and are not exposed to the
production agent tool registry.
"""

import os
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request

from agent.events import emit_event

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
