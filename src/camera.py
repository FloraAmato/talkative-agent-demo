"""
Camera utility — captures a single frame from the webcam.
"""

from __future__ import annotations

import base64
import cv2

from src import config
from src.logger import get_logger

log = get_logger()


def capture_frame_b64() -> str:
    """Capture one frame from the webcam and return it as a base64 JPEG."""
    log.info("[THINKING]   📷 Capturing image from webcam …")
    cap = cv2.VideoCapture(config.CAMERA_DEVICE)
    try:
        if not cap.isOpened():
            raise RuntimeError("Cannot open webcam")
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("Failed to capture frame")
        _, buf = cv2.imencode(".jpg", frame)
        return base64.b64encode(buf.tobytes()).decode("utf-8")
    finally:
        cap.release()
