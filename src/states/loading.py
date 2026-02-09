"""
LOADING state — pre-load every model so subsequent states are instant.
"""

from __future__ import annotations

import subprocess
import requests
import whisper

from src import config
from src.fsm import State
from src.logger import get_logger

log = get_logger()


class LoadingHandler:
    """Warms up Whisper, OpenWakeWord, Piper, and pings Ollama."""

    def __init__(self) -> None:
        self.whisper_model = None
        self.oww_model = None

    def __call__(self) -> tuple[State, dict]:
        log.info("[LOADING] Warming up models …")

        # --- Whisper ---
        log.info("[LOADING]   • Whisper (%s) …", config.WHISPER_MODEL)
        self.whisper_model = whisper.load_model(config.WHISPER_MODEL)

        # --- OpenWakeWord ---
        log.info("[LOADING]   • OpenWakeWord (%s) …", config.WAKE_MODEL)
        from openwakeword.model import Model as OWWModel

        self.oww_model = OWWModel(
            wakeword_models=[config.WAKE_MODEL],
            inference_framework="onnx",
        )

        # --- Piper: download voice if not cached ---
        log.info("[LOADING]   • Piper voice (%s) …", config.PIPER_MODEL)
        self._ensure_piper_voice()

        # --- Ollama: pull model if needed and warm up ---
        log.info("[LOADING]   • Ollama model (%s) …", config.OLLAMA_MODEL)
        self._warm_ollama()

        log.info("[LOADING] All models ready!")
        return State.LISTENING, {
            "whisper_model": self.whisper_model,
            "oww_model": self.oww_model,
        }

    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_piper_voice() -> None:
        """Download the Piper voice model if it isn't already on disk."""
        import os
        os.makedirs(config.PIPER_DATA_DIR, exist_ok=True)
        onnx_path = os.path.join(
            config.PIPER_DATA_DIR, f"{config.PIPER_MODEL}.onnx"
        )
        if not os.path.exists(onnx_path):
            log.info("[LOADING]     Downloading Piper voice …")
            base = (
                "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
                f"it/it_IT/riccardo/x_low/{config.PIPER_MODEL}.onnx"
            )
            for url, dest in [
                (base, onnx_path),
                (base + ".json", onnx_path + ".json"),
            ]:
                resp = requests.get(url, timeout=120)
                resp.raise_for_status()
                with open(dest, "wb") as f:
                    f.write(resp.content)

    @staticmethod
    def _warm_ollama() -> None:
        """Pull the model if absent, then send a throwaway prompt."""
        api = config.OLLAMA_HOST + "/api"

        # Check if model is available, pull if not
        try:
            resp = requests.post(
                f"{api}/show",
                json={"name": config.OLLAMA_MODEL},
                timeout=10,
            )
            if resp.status_code == 404:
                log.info("[LOADING]     Pulling model (this may take a while) …")
                requests.post(
                    f"{api}/pull",
                    json={"name": config.OLLAMA_MODEL, "stream": False},
                    timeout=600,
                )
        except requests.ConnectionError:
            log.warning("[LOADING]     Ollama not reachable — will retry at runtime")
            return

        # Warm-up inference so weights are loaded into memory
        try:
            requests.post(
                f"{api}/generate",
                json={
                    "model": config.OLLAMA_MODEL,
                    "prompt": "ciao",
                    "stream": False,
                },
                timeout=120,
            )
        except Exception:
            pass
