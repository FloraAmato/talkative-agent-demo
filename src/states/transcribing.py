"""
TRANSCRIBING state — convert the captured audio to text using Whisper.
"""

from __future__ import annotations

import numpy as np

from src import config
from src.fsm import State
from src.logger import get_logger

log = get_logger()


class TranscribingHandler:
    """Takes audio numpy array and returns transcribed text."""

    def __init__(self) -> None:
        self.whisper_model = None
        self.audio: np.ndarray | None = None

    def set_context(self, ctx: dict) -> None:
        self.whisper_model = ctx.get("whisper_model", self.whisper_model)
        self.audio = ctx.get("audio", self.audio)

    def __call__(self) -> tuple[State, dict]:
        log.info("[TRANSCRIBING] Running Whisper …")
        result = self.whisper_model.transcribe(
            self.audio,
            language=config.WHISPER_LANGUAGE,
            fp16=False,
        )
        text: str = result["text"].strip()
        log.info("[TRANSCRIBING] \"%s\"", text)

        if not text:
            log.warning("[TRANSCRIBING] Empty transcription — going back to listening")
            return State.THINKING, {"text": ""}

        return State.THINKING, {"text": text}
