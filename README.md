# Talkative Agent — FSM Demo

An Italian-speaking voice assistant built as a **Finite State Machine**, designed for live demos with Italian students.
It listens for a wake word, transcribes speech, thinks via a multimodal LLM (with optional webcam vision), and speaks the answer back — all running locally.

## Architecture

```
┌──────────┐     ┌───────────┐     ┌──────────────┐     ┌──────────┐     ┌──────────┐
│ LOADING  │────>│ LISTENING │────>│ TRANSCRIBING │────>│ THINKING │────>│ SPEAKING │
│ (warm-up)│     │(wake word)│     │  (Whisper)   │     │ (Ollama) │     │ (Piper)  │
└──────────┘     └───────────┘     └──────────────┘     └──────────┘     └──────────┘
                       ^                                      │                │
                       │              ┌────────┐              │                │
                       │              │ CAMERA │<─────────────┘ (tool call)    │
                       │              └────────┘                               │
                       └───────────────────────────────────────────────────────┘
```

### States

| State | Component | Purpose |
|---|---|---|
| **LOADING** | Whisper, OpenWakeWord, Piper, Ollama | Pre-load all models once at startup |
| **LISTENING** | OpenWakeWord + PyAudio | Detect wake word ("Hey Jarvis"), then record until silence |
| **TRANSCRIBING** | Whisper (`base`) | Speech-to-text in Italian |
| **THINKING** | Ollama (`llava:7b`) | Agentic LLM — can invoke a camera tool to see the environment |
| **SPEAKING** | Piper (`it_IT-riccardo-x_low`) | Text-to-speech in Italian, streamed to speakers |

### Camera Tool (Agentic Behavior)

The LLM is given a `capture_image` tool. When the user asks to *look at* or *describe* something, the model invokes the tool, a webcam frame is captured and appended to the conversation as an image, and the model responds based on what it sees.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- NVIDIA GPU + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) (for Ollama)
- USB webcam (e.g., Logitech) at `/dev/video0`
- Working PulseAudio (microphone + speakers)

### Run

```bash
docker compose up --build
```

On first run, the LOADING state will download:
- The Whisper `base` model (~140 MB)
- The `llava:7b` Ollama model (~4.5 GB)
- The Piper Italian voice (~15 MB)

Subsequent runs are instant thanks to Docker volumes.

### Interact

1. Wait for `[LOADING] All models ready!`
2. Say **"Hey Jarvis"**
3. Ask a question in Italian (e.g., *"Che tempo fa oggi?"*)
4. Ask it to look at something (e.g., *"Cosa vedi davanti a te?"*) — it will use the webcam
5. Listen to the spoken response

## Configuration

All settings are in `src/config.py` and overridable via environment variables:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://ollama:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llava:7b` | Multimodal model for reasoning |
| `WHISPER_MODEL` | `base` | Whisper model size (`tiny`, `base`, `small`, …) |
| `WAKE_MODEL` | `hey_jarvis` | OpenWakeWord wake word model |
| `WAKE_THRESHOLD` | `0.5` | Wake word confidence threshold |
| `SILENCE_TIMEOUT` | `1.5` | Seconds of silence before stop recording |
| `SILENCE_THRESHOLD` | `500` | Amplitude below which audio is "silent" |
| `CAMERA_DEVICE` | `0` | OpenCV camera device index |

## Project Structure

```
.
├── main.py                  # Entrypoint — wires up the FSM
├── src/
│   ├── fsm.py               # FSM engine (states, transitions, loop)
│   ├── logger.py             # Colored per-state logging
│   ├── config.py             # Centralised configuration
│   ├── camera.py             # Webcam capture utility
│   └── states/
│       ├── loading.py        # LOADING — model warm-up
│       ├── listening.py      # LISTENING — wake word + audio capture
│       ├── transcribing.py   # TRANSCRIBING — Whisper STT
│       ├── thinking.py       # THINKING — Ollama agentic LLM
│       └── speaking.py       # SPEAKING — Piper TTS
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Colored Logging

Each state logs in a distinct terminal colour for easy visual tracking:

- 🟣 **LOADING** — magenta
- 🔵 **LISTENING** — cyan
- 🟡 **TRANSCRIBING** — yellow
- 🟢 **THINKING** — green
- 🔵 **SPEAKING** — blue
- 🔴 **ERROR** — red
