FROM python:3.11-slim

# System deps for PyAudio, OpenCV, and general build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        portaudio19-dev \
        libsndfile1 \
        ffmpeg \
        libgl1 \
        libglib2.0-0 \
        alsa-utils \
        pulseaudio-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Piper TTS binary
RUN pip install --no-cache-dir piper-tts

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-create model cache dirs
RUN mkdir -p /app/models/piper

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
