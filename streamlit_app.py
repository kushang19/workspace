import html
import streamlit as st

from app import create_messages, run_agent_turn, set_event_callback, stop_react_app


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="React AI Agent",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = create_messages()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "running_project" not in st.session_state:
    st.session_state.running_project = None


# ============================================================
# SIMPLE STYLING
# ============================================================

st.markdown(
    """
    <style>
        .agent-log {
            border: 1px solid rgba(128,128,128,.25);
            border-radius: 10px;
            padding: 12px 14px;
            background: rgba(128,128,128,.06);
            font-family: monospace;
            font-size: 13px;
            line-height: 1.55;
            max-height: 420px;
            overflow-y: auto;
        }
        .log-muted { opacity: .7; }
        .log-success { font-weight: 600; }
        .run-button {
            display: inline-block;
            padding: 9px 14px;
            border-radius: 7px;
            text-decoration: none !important;
            border: 1px solid rgba(128,128,128,.35);
            font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

col1, col2 = st.columns([4, 1])

with col1:
    st.title("🤖 React AI Agent")
    st.caption("Describe an application and watch the agent build it step by step.")

with col2:
    if st.session_state.running_project:
        st.success("🟢 App running")


# ============================================================
# RUNNING PROJECT CONTROLS
# ============================================================

if st.session_state.running_project:
    running = st.session_state.running_project

    st.subheader("🚀 Running Project")

    project_col, action_col = st.columns([4, 1])

    with project_col:
        project_name = running.get("project_name", "React project")
        url = running.get("url", "http://localhost:5173")

        st.write(f"**{project_name}**")

        # target=_blank opens the generated React app in a new browser tab.
        safe_url = html.escape(url, quote=True)
        st.markdown(
            f'<a class="run-button" href="{safe_url}" target="_blank">🌐 Open React App ↗</a>',
            unsafe_allow_html=True
        )

    with action_col:
        st.write("")
        st.write("")

        if st.button(
            "⏹ Terminate App",
            type="secondary",
            use_container_width=True
        ):
            result = stop_react_app(running["pid"])

            if result.get("success"):
                st.session_state.running_project = None
                st.success("React development server terminated.")
                st.rerun()
            else:
                st.error(result.get("error", "Could not terminate the app."))

    st.divider()


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# LIVE AGENT LOG
# ============================================================

log_container = st.container()
live_events = []


def render_live_event(event):
    """Render observable agent activity as it arrives."""

    live_events.append(event)

    lines = []

    for item in live_events:
        step = item.get("step")

        if step == "plan":
            lines.append(f"🧠  PLAN      {item.get('content', '')}")

        elif step == "action":
            function_name = item.get("function", "unknown")
            content = item.get("content", "")
            if content:
                lines.append(f"🛠️  ACTION    {content} [{function_name}]")
            else:
                lines.append(f"🛠️  ACTION    {function_name}")

        elif step == "command_start":
            command = " ".join(item.get("command", []))
            lines.append(f"   ├─ $ {command}")

        elif step == "command_output":
            line = item.get("line", "")
            if line:
                lines.append(f"   │  {line}")

        elif step == "observation":
            observation = item.get("observation", {})
            if observation.get("success"):
                lines.append("   └─ ✓ Tool completed successfully")
            else:
                error = observation.get("error", "Tool execution failed")
                lines.append(f"   └─ ✗ {error}")

        elif step == "server_starting":
            lines.append(
                f"🚀  SERVER    Starting React app on port {item.get('port', 5173)} "
                f"(PID {item.get('pid')})"
            )

        elif step == "server_stopped":
            lines.append(f"⏹  SERVER    React app stopped (PID {item.get('pid')})")

    escaped = html.escape("\n".join(lines))

    with log_container:
        st.markdown(
            f'<div class="agent-log">{escaped}</div>',
            unsafe_allow_html=True
        )


# ============================================================
# USER INPUT
# ============================================================

prompt = st.chat_input("What do you want to build?")


# ============================================================
# PROCESS USER INPUT
# ============================================================

if prompt:

    st.session_state.chat_history.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        status_placeholder = st.empty()

        # Connect app.py's live event stream to this Streamlit run.
        set_event_callback(render_live_event)

        try:
            with status_placeholder.status(
                "🤖 Agent is working...",
                expanded=True
            ):
                result = run_agent_turn(
                    prompt,
                    st.session_state.messages
                )

            # ----------------------------------------------------
            # QUESTION
            # ----------------------------------------------------

            if result["status"] == "question":
                response_text = result["content"]

                st.markdown(response_text)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_text
                })

            # ----------------------------------------------------
            # FINAL OUTPUT
            # ----------------------------------------------------

            elif result["status"] == "output":
                response_text = result["content"]
                project = result.get("project", {})
                files = result.get("files", [])

                st.success(response_text)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_text
                })

                # Save running project details for the controls above.
                # The actual PID/url comes from the start_react_app observation.
                for event in result.get("events", []):
                    if event.get("step") == "observation" and event.get("function") == "start_react_app":
                        observation = event.get("observation", {})
                        if observation.get("success"):
                            st.session_state.running_project = {
                                "project_name": project.get("name", "React project"),
                                "project_path": observation.get("project_path", ""),
                                "pid": observation.get("pid"),
                                "port": observation.get("port", 5173),
                                "url": observation.get("url", "http://localhost:5173")
                            }
                        break

                if project:
                    with st.expander("📦 Project details"):
                        st.json(project)

                if files:
                    with st.expander(f"📁 Created files ({len(files)})"):
                        for file in files:
                            st.code(file)

            # ----------------------------------------------------
            # ERROR
            # ----------------------------------------------------

            else:
                response_text = result["content"]
                st.error(response_text)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_text
                })

        finally:
            # Do not leave a callback pointing at an old Streamlit run.
            set_event_callback(None)
