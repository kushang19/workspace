import html
import io
import re
import zipfile
from pathlib import Path

import streamlit as st

from app import (
    create_messages,
    run_agent_turn,
    set_event_callback,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="React AI Agent",
    page_icon="🤖",
    layout="wide",
)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = create_messages()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "projects" not in st.session_state:
    st.session_state.projects = {}


# ============================================================
# STYLING
# ============================================================

st.markdown(
    """
    <style>
        .project-card {
            border: 1px solid rgba(128,128,128,.25);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            background: rgba(128,128,128,.05);
        }

        .live-card {
            border: 1px solid rgba(128,128,128,.25);
            border-radius: 12px;
            padding: 14px 16px;
            background: rgba(128,128,128,.05);
            font-family: monospace;
            font-size: 13px;
            line-height: 1.55;
            min-height: 58px;
            animation: live-slide .22s ease-out;
        }

        @keyframes live-slide {
            from {
                opacity: 0;
                transform: translateY(5px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .status-running {
            font-weight: 600;
        }

        .status-stopped {
            opacity: .65;
        }

        .open-app {
            display: inline-block;
            padding: 8px 13px;
            border-radius: 7px;
            text-decoration: none !important;
            border: 1px solid rgba(128,128,128,.35);
            font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def project_key(project_path, project_name):
    return project_path or project_name


def safe_project_filename(project_name):
    """Return a filesystem-safe project name for the ZIP download."""
    name = re.sub(r"[^A-Za-z0-9._ -]+", "", project_name or "react-project")
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name or "react-project"


def create_project_zip(project_path):
    """Create an in-memory ZIP of the generated project source files."""
    root = Path(project_path)
    data = io.BytesIO()

    excluded = {"node_modules", "dist", ".git", ".vite", ".react-agent-dev.log"}

    with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue

            relative = file_path.relative_to(root)
            if any(part in excluded for part in relative.parts):
                continue

            archive.write(file_path, relative.as_posix())

    data.seek(0)
    return data.getvalue()


def register_project(project_name, project_path, url):
    key = project_key(project_path, project_name)

    st.session_state.projects[key] = {
        "project_name": project_name or "React project",
        "project_path": project_path,
        "url": url,
        "deployed": bool(url),
    }


def register_project_from_result(result):
    project = result.get("project") or {}
    project_name = project.get("name", "React project")

    for event in result.get("events", []):
        if event.get("step") != "observation":
            continue

        if event.get("function") != "deploy_to_cloudflare_pages":
            continue

        observation = event.get("observation") or {}

        if observation.get("success"):
            register_project(
                project_name=project_name,
                project_path=observation.get("project_path", ""),
                url=observation.get("url", ""),
            )

        break


def render_live_event(event, placeholder):
    """
    Show ONLY the newest event in the live area.

    Every event is also stored in agent_log_history for the
    full log history view.
    """

    if "agent_log_history" not in st.session_state:
        st.session_state.agent_log_history = []

    st.session_state.agent_log_history.append(event)

    step = event.get("step")
    title = "Agent"
    body = ""

    if step == "plan":
        title = "🧠 Planning"
        body = event.get("content", "")

    elif step == "action":
        function_name = event.get("function", "unknown")
        title = "🛠️ Working"
        body = event.get("content") or function_name

    elif step == "command_start":
        title = "⚙️ Running command"
        command = " ".join(event.get("command", []))
        body = f"$ {command}"

    elif step == "command_output":
        title = "📟 Command output"
        body = event.get("line", "")

    elif step == "observation":
        function_name = event.get("function", "tool")
        observation = event.get("observation") or {}

        if observation.get("success"):
            title = "✓ Tool completed"
            body = function_name
        else:
            title = "✗ Tool failed"
            body = observation.get(
                "error",
                "Tool execution failed."
            )

    else:
        title = step or "Agent"
        body = event.get("content", "")

    escaped_title = html.escape(str(title))
    escaped_body = html.escape(str(body))

    placeholder.markdown(
        f"""
        <div class="live-card">
            <strong>{escaped_title}</strong><br>
            {escaped_body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_full_history():
    history = st.session_state.get(
        "agent_log_history",
        []
    )

    if not history:
        st.info("No agent activity yet.")
        return

    for index, event in enumerate(history, start=1):
        step = event.get("step", "event")

        if step == "command_output":
            text = event.get("line", "")
            if text:
                st.code(text, language="text")

        elif step == "command_start":
            command = " ".join(event.get("command", []))
            st.write(f"**⚙️ Command:** `{command}`")

        elif step == "action":
            function_name = event.get("function", "unknown")
            content = event.get("content", "")
            st.write(
                f"**🛠️ {function_name}**"
                + (f" — {content}" if content else "")
            )

        elif step == "plan":
            st.write(
                f"**🧠 Plan:** {event.get('content', '')}"
            )

        elif step == "observation":
            function_name = event.get("function", "tool")
            observation = event.get("observation") or {}

            if observation.get("success"):
                st.write(
                    f"**✓ {function_name} completed**"
                )
            else:
                st.error(
                    f"{function_name}: "
                    f"{observation.get('error', 'failed')}"
                )

        else:
            st.write(
                f"**{step}:** "
                f"{event.get('content', '')}"
            )

        if index < len(history):
            st.divider()


# ============================================================
# HEADER
# ============================================================

st.title("🤖 React AI Agent")
st.caption(
    "Describe an application and watch the agent build it."
)


# ============================================================
# PROJECT MANAGER
# ============================================================

projects = st.session_state.projects

if projects:
    st.subheader("🚀 Projects")

    for key, project in list(projects.items()):

        name = project.get("project_name", "React project")
        url = project.get("url", "")
        deployed = project.get("deployed", False)

        with st.container(border=True):

            status_text = "🟢 Deployed" if deployed else "⚪ Not deployed"

            st.markdown(
                f"### {name} &nbsp; "
                f"<span class='{'status-running' if deployed else 'status-stopped'}'>"
                f"{status_text}</span>",
                unsafe_allow_html=True,
            )

            if deployed and url:
                safe_url = html.escape(url, quote=True)

                st.markdown(
                    f'<a class="open-app" '
                    f'href="{safe_url}" '
                    f'target="_blank">'
                    f'🌐 Open App ↗'
                    f'</a>',
                    unsafe_allow_html=True,
                )

                st.caption(f"`{url}`")
            else:
                st.write("Deployment unavailable.")

            project_path = project.get("project_path", "")

            if project_path and Path(project_path).is_dir():
                try:
                    zip_data = create_project_zip(project_path)
                    download_name = (
                        f"{safe_project_filename(name)}.zip"
                    )

                    st.download_button(
                        f"⬇️ Download {download_name}",
                        data=zip_data,
                        file_name=download_name,
                        mime="application/zip",
                        key=f"download_{key}",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.error(f"Could not create ZIP: {exc}")
            else:
                st.caption("ZIP unavailable")

    st.divider()


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# LIVE AGENT ACTIVITY
# ============================================================

# Keep the live agent message immediately above the chat input.
st.subheader("⚡ Agent Activity")

live_placeholder = st.empty()

if "agent_log_history" not in st.session_state:
    st.session_state.agent_log_history = []

history_button_label = (
    "📜 Hide Log History"
    if st.session_state.get("show_log_history", False)
    else "📜 View Log History"
)

if st.button(
    history_button_label,
    key="toggle_history",
):
    st.session_state.show_log_history = not st.session_state.get(
        "show_log_history",
        False
    )
    st.rerun()

if st.session_state.get("show_log_history", False):
    with st.expander(
        "Complete Agent Log",
        expanded=True,
    ):
        render_full_history()


# ============================================================
# USER INPUT
# ============================================================

prompt = st.chat_input(
    "What do you want to build?"
)


# ============================================================
# PROCESS USER INPUT
# ============================================================

if prompt:

    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        status_placeholder = st.empty()
        status_placeholder.info("🤖 Agent is working...")

        # Clear the current live event before this run.
        live_placeholder.empty()

        def live_callback(event):
            render_live_event(
                event,
                live_placeholder,
            )

        set_event_callback(live_callback)

        try:
            result = run_agent_turn(
                prompt,
                st.session_state.messages,
            )

            if result["status"] == "question":

                status_placeholder.empty()

                response_text = result["content"]

                st.markdown(response_text)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": response_text,
                    }
                )

            elif result["status"] == "output":

                status_placeholder.empty()

                response_text = result["content"]

                st.success(response_text)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": response_text,
                    }
                )

                register_project_from_result(
                    result
                )

                project = result.get(
                    "project",
                    {}
                )

                files = result.get(
                    "files",
                    []
                )

                if project:
                    with st.expander(
                        "📦 Project details"
                    ):
                        st.json(project)

                if files:
                    with st.expander(
                        f"📁 Created files ({len(files)})"
                    ):
                        for file in files:
                            st.code(file)

            else:

                status_placeholder.empty()

                response_text = result["content"]

                st.error(response_text)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": response_text,
                    }
                )

        finally:
            set_event_callback(None)
