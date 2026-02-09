"""
LISTENING state — wait for the wake word, then capture the full utterance.

Uses OpenWakeWord for detection and PyAudio for capture.
"""

from __future__ import annotations

import struct
import numpy as np
import pyaudio

from src import config
from src.fsm import State
from src.logger import get_logger

log = get_logger()


class ListeningHandler:
    """Blocks until the wake word is heard, then records until silence."""

    def __init__(self) -> None:
        self.oww_model = None
        self._pa: pyaudio.PyAudio | None = None

    def set_context(self, ctx: dict) -> None:
        self.oww_model = ctx.get("oww_model", self.oww_model)

    # ------------------------------------------------------------------
    def __call__(self) -> tuple[State, dict]:
        log.info("[LISTENING] Waiting for wake word …")

        self._pa = pyaudio.PyAudio()
        stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=config.CHANNELS,
            rate=config.SAMPLE_RATE,
            input=True,
            frames_per_buffer=config.CHUNK_SIZE,
        )

        try:
            self._wait_for_wake_word(stream)
            log.info("[LISTENING] Wake word detected! Recording …")
            audio = self._record_until_silence(stream)
        finally:
            stream.stop_stream()
            stream.close()

        return State.TRANSCRIBING, {"audio": audio}

    # ------------------------------------------------------------------
    def _wait_for_wake_word(self, stream: pyaudio.Stream) -> None:
        while True:
            chunk = stream.read(config.CHUNK_SIZE, exception_on_overflow=False)
            audio_arr = np.frombuffer(chunk, dtype=np.int16)
            prediction = self.oww_model.predict(audio_arr)

            for mdl_name, score in prediction.items():
                if score >= config.WAKE_THRESHOLD:
                    self.oww_model.reset()
                    return

    def _record_until_silence(self, stream: pyaudio.Stream) -> np.ndarray:
        """Record audio frames until sustained silence is detected."""
        frames: list[bytes] = []
        silent_chunks = 0
        chunks_for_timeout = int(
            config.SILENCE_TIMEOUT * config.SAMPLE_RATE / config.CHUNK_SIZE
        )

        while True:
            chunk = stream.read(config.CHUNK_SIZE, exception_on_overflow=False)
            frames.append(chunk)

            # simple energy-based silence detection
            samples = np.frombuffer(chunk, dtype=np.int16)
            energy = int(np.abs(samples).mean())

            if energy < config.SILENCE_THRESHOLD:
                silent_chunks += 1
            else:
                silent_chunks = 0

            if silent_chunks >= chunks_for_timeout:
                break

        raw = b"".join(frames)
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        log.info("[LISTENING] Captured %.1f s of audio", len(audio) / config.SAMPLE_RATE)
        return audio
