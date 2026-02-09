"""
Finite State Machine engine.

States:
    LOADING       -> LISTENING      (models warmed up)
    LISTENING     -> TRANSCRIBING   (wake word detected, speech captured)
    TRANSCRIBING  -> THINKING       (text ready)
    THINKING      -> SPEAKING       (response ready)
    SPEAKING      -> LISTENING      (utterance finished)

Any state can transition to ERROR, which falls back to LISTENING.
"""

from __future__ import annotations

import enum
import time
from typing import Any

from src.logger import get_logger

log = get_logger()


class State(enum.Enum):
    LOADING = "LOADING"
    LISTENING = "LISTENING"
    TRANSCRIBING = "TRANSCRIBING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"


# Allowed transitions
TRANSITIONS: dict[State, list[State]] = {
    State.LOADING: [State.LISTENING],
    State.LISTENING: [State.TRANSCRIBING],
    State.TRANSCRIBING: [State.THINKING],
    State.THINKING: [State.SPEAKING],
    State.SPEAKING: [State.LISTENING],
    State.ERROR: [State.LISTENING],
}


class FSMError(Exception):
    pass


class TalkativeFSM:
    """Drives the agent through its states in a loop."""

    def __init__(self, handlers: dict[State, Any]) -> None:
        self.state = State.LOADING
        self.handlers = handlers
        self._running = False

    def _transition(self, target: State) -> None:
        allowed = TRANSITIONS.get(self.state, [])
        if target not in allowed and target != State.ERROR:
            raise FSMError(
                f"Invalid transition {self.state.value} -> {target.value}"
            )
        log.info(f"[{self.state.value}] -> [{target.value}]")
        self.state = target

    def run(self) -> None:
        """Main loop — runs until interrupted."""
        self._running = True
        log.info(f"[{self.state.value}] FSM started")

        while self._running:
            handler = self.handlers.get(self.state)
            if handler is None:
                raise FSMError(f"No handler for state {self.state.value}")
            try:
                next_state, context = handler()
                self._transition(next_state)
                # pass context into the next handler if it accepts it
                next_handler = self.handlers.get(self.state)
                if next_handler and hasattr(next_handler, "set_context"):
                    next_handler.set_context(context)
            except KeyboardInterrupt:
                log.info(f"[{self.state.value}] Interrupted — shutting down")
                self._running = False
            except Exception as exc:
                log.error(f"[ERROR] In {self.state.value}: {exc}")
                self.state = State.ERROR
                # small back-off before retrying
                time.sleep(1)
                self._transition(State.LISTENING)
