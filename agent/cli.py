"""Command-line interface for the React AI Agent."""

import json

from agent.state import create_messages
from agent.turn import run_agent_turn

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
