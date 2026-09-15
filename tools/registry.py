"""Central registry of tools exposed to the agent."""

from tools.react_project import (
    create_react_project,
    run_command,
    install_dependencies,
    install_package,
)
from tools.filesystem import write_file, read_file, list_directory
from tools.cloudflare import deploy_to_cloudflare_pages

available_tools = {
    "create_react_project": create_react_project,
    "run_command": run_command,
    "write_file": write_file,
    "read_file": read_file,
    "list_directory": list_directory,
    "install_dependencies": install_dependencies,
    "install_package": install_package,
    "deploy_to_cloudflare_pages": deploy_to_cloudflare_pages,
}
