"""
SPEAKING state — read the LLM response aloud using Piper TTS + PyAudio.

Piper is invoked as a subprocess piping WAV data, which we stream to the
speakers through PyAudio for low-latency playback.
"""

from __future__ import annotations

import subprocess
import wave
import io

import pyaudio

from src import config
from src.fsm import State
from src.logger import get_logger

log = get_logger()


class SpeakingHandler:
    """Synthesise speech with Piper and play it."""

    def __init__(self) -> None:
        self.response: str = ""

    def set_context(self, ctx: dict) -> None:
        self.response = ctx.get("response", "")

    def __call__(self) -> tuple[State, dict]:
        if not self.response:
            log.info("[SPEAKING] Nothing to say — back to listening")
            return State.LISTENING, {}

        log.info("[SPEAKING] Speaking …")
        wav_bytes = self._synthesise(self.response)
        self._play(wav_bytes)
        log.info("[SPEAKING] Done")
        return State.LISTENING, {}

    # ------------------------------------------------------------------
    @staticmethod
    def _synthesise(text: str) -> bytes:
        """Run Piper as a subprocess and return raw WAV bytes."""
        model_path = f"{config.PIPER_DATA_DIR}/{config.PIPER_MODEL}.onnx"
        cmd = [
            "piper",
            "--model", model_path,
            "--output-raw",
        ]
        proc = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=30,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Piper failed: {proc.stderr.decode()}")
        return proc.stdout

    @staticmethod
    def _play(raw_pcm: bytes) -> None:
        """Play raw 16-bit mono PCM through the default audio output."""
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=config.PIPER_SAMPLE_RATE,
            output=True,
        )
        try:
            # Stream in small chunks so we don't block for too long
            chunk = 4096
            for i in range(0, len(raw_pcm), chunk):
                stream.write(raw_pcm[i : i + chunk])
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()
