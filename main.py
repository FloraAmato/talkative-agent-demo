#!/usr/bin/env python3
"""
Talkative Agent — an FSM-driven, Italian-speaking voice assistant.

Run:
    python main.py
"""

from src.fsm import State, TalkativeFSM
from src.states.loading import LoadingHandler
from src.states.listening import ListeningHandler
from src.states.transcribing import TranscribingHandler
from src.states.thinking import ThinkingHandler
from src.states.speaking import SpeakingHandler
from src.logger import get_logger

log = get_logger()


def main() -> None:
    # Instantiate handlers (they hold their own state / loaded models)
    loading = LoadingHandler()
    listening = ListeningHandler()
    transcribing = TranscribingHandler()
    thinking = ThinkingHandler()
    speaking = SpeakingHandler()

    # After LOADING, share the pre-loaded models with subsequent handlers
    class LoadingBridge:
        """Wraps LoadingHandler to propagate models to downstream handlers."""

        def __call__(self):
            next_state, ctx = loading()
            # propagate shared models
            listening.set_context(ctx)
            transcribing.whisper_model = ctx["whisper_model"]
            return next_state, ctx

    fsm = TalkativeFSM(
        handlers={
            State.LOADING: LoadingBridge(),
            State.LISTENING: listening,
            State.TRANSCRIBING: transcribing,
            State.THINKING: thinking,
            State.SPEAKING: speaking,
        }
    )

    log.info("[LOADING] === Talkative Agent (FSM) ===")
    fsm.run()


if __name__ == "__main__":
    main()
