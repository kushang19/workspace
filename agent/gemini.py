"""Gemini client and response helpers."""

import json
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from agent.events import emit_event

load_dotenv()

client = genai.Client(
    http_options=types.HttpOptions(
        timeout=15000,
        retry_options=types.HttpRetryOptions(
            attempts=1
        ),
    )
)

def call_gemini(messages, system_prompt):
    """
    Call Gemini with a short, controlled retry policy.

    The SDK normally retries transient 5xx/429 errors automatically.
    For this interactive agent we disable those hidden retries and
    handle a small number of retries ourselves so the UI does not
    appear stuck for a long time.
    """

    full_prompt = f"{system_prompt}\\n\\n"

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if role == "system":
            continue
        elif role == "user":
            full_prompt += f"User: {content}\\n\\n"
        elif role == "assistant":
            full_prompt += f"Assistant: {content}\\n\\n"

    full_prompt += "Assistant: "

    max_attempts = 2
    retry_delays = [1.0]

    for attempt in range(max_attempts):
        try:
            emit_event({
                "step": "gemini",
                "content": (
                    "Contacting Gemini..."
                    if attempt == 0
                    else "Gemini is temporarily busy. Retrying..."
                ),
                "function": None,
                "input": {},
            })

            print(
                f"\\n🤖 Gemini request "
                f"(attempt {attempt + 1}/{max_attempts})"
            )

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=full_prompt
            )

            if response.text:
                return response.text

            raise RuntimeError("Gemini returned an empty response.")

        except Exception as error:
            error_text = str(error)

            print(
                f"\\n❌ Gemini API Error "
                f"(attempt {attempt + 1}/{max_attempts}):\\n{error_text}"
            )

            is_transient = any(
                code in error_text
                for code in (
                    "503",
                    "429",
                    "500",
                    "502",
                    "504",
                    "UNAVAILABLE",
                    "RESOURCE_EXHAUSTED",
                )
            )

            if not is_transient or attempt == max_attempts - 1:
                return None

            delay = retry_delays[attempt]

            emit_event({
                "step": "gemini_retry",
                "content": f"Gemini is busy. Retrying in {delay:.0f}s...",
                "function": None,
                "input": {},
            })

            time.sleep(delay)

    return None

def clean_json_response(raw_response):
    """
    Clean the raw response from Gemini to extract valid JSON.
    Handles: markdown fences, leading/trailing text, multiple concatenated
    JSON objects (returns only the first valid one).
    """
    if raw_response is None:
        return None

    raw_response = raw_response.strip()

    # Remove markdown code blocks if present
    if raw_response.startswith("```json"):
        raw_response = raw_response[7:]
    elif raw_response.startswith("```"):
        raw_response = raw_response[3:]

    if raw_response.endswith("```"):
        raw_response = raw_response[:-3]

    raw_response = raw_response.strip()

    # Find the first balanced JSON object using brace counting
    start = raw_response.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(raw_response)):
        ch = raw_response[i]

        if escape:
            escape = False
            continue

        if ch == "\\":
            escape = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                # Found the end of the first complete JSON object
                return raw_response[start:i + 1]

    return None
