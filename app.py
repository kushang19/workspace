"""React AI Agent application facade.

The implementation is split into focused modules. This file provides the
public application-level imports and the CLI entry point.
"""

from agent.events import emit_event, set_event_callback
from agent.state import create_messages, add_message
from agent.turn import run_agent_turn
from agent.cli import run_cli

# Local-development helpers are intentionally available for callers that need
# them, but they are not included in tools.registry.available_tools.
from tools.react_server import (
    find_available_port,
    wait_for_server,
    start_react_app,
    stop_react_app,
)

__all__ = [
    "emit_event",
    "set_event_callback",
    "create_messages",
    "add_message",
    "run_agent_turn",
    "run_cli",
    "find_available_port",
    "wait_for_server",
    "start_react_app",
    "stop_react_app",
]

if __name__ == "__main__":
    run_cli()
