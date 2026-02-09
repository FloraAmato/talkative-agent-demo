"""
THINKING state — send the user prompt to Ollama (agentic, with camera tool).

Flow:
  1. Send user text to the model with tool definitions.
  2. If the model invokes the "capture_image" tool, take a photo and
     re-prompt with the image attached.
  3. Return the final text response.
"""

from __future__ import annotations

import json
import requests

from src import config
from src.camera import capture_frame_b64
from src.fsm import State
from src.logger import get_logger

log = get_logger()

# Tool definition exposed to the model
CAMERA_TOOL = {
    "type": "function",
    "function": {
        "name": "capture_image",
        "description": (
            "Scatta una foto con la webcam per vedere cosa c'è davanti a te. "
            "Usalo quando l'utente chiede di guardare, vedere, o descrivere "
            "qualcosa nell'ambiente circostante."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}

MAX_TOOL_ROUNDS = 3  # safety cap


class ThinkingHandler:
    """Agentic LLM call with optional camera tool."""

    def __init__(self) -> None:
        self.text: str = ""

    def set_context(self, ctx: dict) -> None:
        self.text = ctx.get("text", "")

    # ------------------------------------------------------------------
    def __call__(self) -> tuple[State, dict]:
        if not self.text:
            return State.SPEAKING, {"response": ""}

        log.info("[THINKING] Prompt: \"%s\"", self.text)

        messages = [
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": self.text},
        ]

        response_text = self._chat_loop(messages)
        log.info("[THINKING] Response: \"%s\"", response_text)
        return State.SPEAKING, {"response": response_text}

    # ------------------------------------------------------------------
    def _chat_loop(self, messages: list[dict]) -> str:
        """Run the chat loop, handling tool calls up to MAX_TOOL_ROUNDS."""
        api = f"{config.OLLAMA_HOST}/api/chat"

        for _ in range(MAX_TOOL_ROUNDS):
            payload = {
                "model": config.OLLAMA_MODEL,
                "messages": messages,
                "tools": [CAMERA_TOOL],
                "stream": False,
            }

            resp = requests.post(api, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()

            msg = data.get("message", {})
            tool_calls = msg.get("tool_calls")

            if not tool_calls:
                return msg.get("content", "").strip()

            # Process tool call(s)
            messages.append(msg)  # assistant's tool-call message

            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                log.info("[THINKING]   Tool call: %s", fn_name)

                if fn_name == "capture_image":
                    image_b64 = capture_frame_b64()
                    # Append image as a new user message with the image
                    messages.append({
                        "role": "tool",
                        "content": "Immagine catturata con successo.",
                    })
                    # Re-send with image embedded in a user message
                    messages.append({
                        "role": "user",
                        "content": "Ecco l'immagine catturata dalla webcam.",
                        "images": [image_b64],
                    })
                else:
                    messages.append({
                        "role": "tool",
                        "content": f"Tool sconosciuto: {fn_name}",
                    })

        # Fell through — ask model to conclude
        messages.append({
            "role": "user",
            "content": "Per favore, rispondi ora con le informazioni che hai.",
        })
        resp = requests.post(
            api,
            json={
                "model": config.OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("message", {}).get("content", "").strip()
