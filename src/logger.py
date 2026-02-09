"""
Colored logging for each FSM state.

Each state gets a distinct color so you can visually follow
the pipeline in the terminal.
"""

import logging
import sys

# ANSI color codes
COLORS = {
    "LOADING":      "\033[95m",   # magenta
    "LISTENING":    "\033[96m",   # cyan
    "TRANSCRIBING": "\033[93m",   # yellow
    "THINKING":     "\033[92m",   # green
    "SPEAKING":     "\033[94m",   # blue
    "ERROR":        "\033[91m",   # red
    "RESET":        "\033[0m",
}


class ColorFormatter(logging.Formatter):
    """Formatter that colours the message based on the state prefix."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        for state, color in COLORS.items():
            if state == "RESET":
                continue
            if msg.startswith(f"[{state}]"):
                return f"{color}{msg}{COLORS['RESET']}"
        return msg


def get_logger(name: str = "talkative") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ColorFormatter("%(message)s"))
        logger.addHandler(handler)
    return logger
