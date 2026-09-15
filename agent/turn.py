"""Core agent turn loop."""

import json

from agent.events import emit_event
from agent.gemini import call_gemini, clean_json_response
from agent.state import add_message
from agent.system_prompt import SYSTEM_PROMPT
from tools.registry import available_tools

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
                    "content": "Gemini is temporarily unavailable. The request was retried, but Gemini did not accept it. Please try again in a few seconds.",
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
