"""Cloudflare Pages deployment tool."""

import json
import os
import subprocess
import urllib.error
import urllib.request

from agent.events import emit_event

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
