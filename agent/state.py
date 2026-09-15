"""Agent conversation state helpers."""

from agent.system_prompt import SYSTEM_PROMPT

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

def add_message(messages, role, content):
    messages.append(
        {
            "role": role,
            "content": content
        }
    )
