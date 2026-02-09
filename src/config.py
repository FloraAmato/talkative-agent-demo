"""
Central configuration — all tunables in one place.
"""

import os

# ---------------------------------------------------------------------------
# Ollama
# ---------------------------------------------------------------------------
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llava:7b")

# System prompt — instruct the model to respond in Italian
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    (
        "Sei un assistente vocale amichevole e disponibile. "
        "Rispondi SEMPRE in italiano, in modo conciso e naturale, "
        "come in una conversazione parlata. "
        "Se ti viene fornita un'immagine, descrivila e rispondi "
        "in base al contesto della conversazione. "
        "Mantieni le risposte brevi (massimo 2-3 frasi) a meno che "
        "non ti venga chiesto esplicitamente di approfondire."
    ),
)

# ---------------------------------------------------------------------------
# Whisper (speech-to-text)
# ---------------------------------------------------------------------------
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
WHISPER_LANGUAGE = "it"

# ---------------------------------------------------------------------------
# Piper (text-to-speech)
# ---------------------------------------------------------------------------
PIPER_MODEL = os.getenv(
    "PIPER_MODEL", "it_IT-riccardo-x_low"
)
PIPER_DATA_DIR = os.getenv("PIPER_DATA_DIR", "/app/models/piper")
PIPER_SAMPLE_RATE = 22050

# ---------------------------------------------------------------------------
# OpenWakeWord
# ---------------------------------------------------------------------------
WAKE_MODEL = os.getenv("WAKE_MODEL", "hey_jarvis")
WAKE_THRESHOLD = float(os.getenv("WAKE_THRESHOLD", "0.5"))

# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1280  # 80 ms at 16 kHz — required by openwakeword

# Silence detection: stop recording after this many seconds of silence
SILENCE_TIMEOUT = float(os.getenv("SILENCE_TIMEOUT", "1.5"))
SILENCE_THRESHOLD = int(os.getenv("SILENCE_THRESHOLD", "500"))

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
CAMERA_DEVICE = int(os.getenv("CAMERA_DEVICE", "0"))
