"""
Camera utility — captures a single frame from the webcam.

Returns None if the camera is not available, so callers can degrade
gracefully (e.g. tell the LLM the webcam is not connected).
"""

from __future__ import annotations

import base64
import cv2

from src import config
from src.logger import get_logger

log = get_logger()


def capture_frame_b64() -> str | None:
    """Capture one frame from the webcam and return it as a base64 JPEG.

    Returns ``None`` if the camera cannot be opened or the frame grab fails.
    """
    log.info("[THINKING]   Capturing image from webcam …")
    try:
        cap = cv2.VideoCapture(config.CAMERA_DEVICE)
        if not cap.isOpened():
            log.warning("[THINKING]   Webcam not available (device %s)", config.CAMERA_DEVICE)
            return None
        ret, frame = cap.read()
        cap.release()
        if not ret:
            log.warning("[THINKING]   Failed to capture frame")
            return None
        _, buf = cv2.imencode(".jpg", frame)
        return base64.b64encode(buf.tobytes()).decode("utf-8")
    except Exception as exc:
        log.warning("[THINKING]   Camera error: %s", exc)
        return None
