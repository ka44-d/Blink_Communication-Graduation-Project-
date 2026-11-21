"""Webcam capture (OpenCV). Frames live only in memory; nothing is written to disk."""
from __future__ import annotations

import logging
import time
from collections.abc import Iterator

import cv2
import numpy as np

from .config import CameraConfig

log = logging.getLogger("blink.capture")


class CameraError(RuntimeError):
    pass


class WebcamCapture:
    def __init__(self, cfg: CameraConfig, max_failures: int = 30) -> None:
        self.cfg, self.max_failures = cfg, max_failures
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        cap = cv2.VideoCapture(self.cfg.index)
        if not cap.isOpened():
            raise CameraError(f"Cannot open camera index {self.cfg.index}. Check it is connected, "
                              "not used by another app, and that camera permission is granted.")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cfg.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cfg.height)
        cap.set(cv2.CAP_PROP_FPS, self.cfg.fps)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._cap = cap
        log.info("Camera %d opened at %dx%d", self.cfg.index,
                 int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    def frames(self) -> Iterator[tuple[np.ndarray, float]]:
        """Yield (BGR frame, monotonic timestamp). NOT mirrored (left/right stay anatomical)."""
        if self._cap is None:
            self.open()
        failures = 0
        while True:
            ok, frame = self._cap.read()
            if not ok or frame is None:
                failures += 1
                if failures >= self.max_failures:
                    raise CameraError("Camera stopped delivering frames.")
                time.sleep(0.02)
                continue
            failures = 0
            yield frame, time.monotonic()

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> "WebcamCapture":
        self.open()
        return self

    def __exit__(self, *exc) -> None:
        self.close()
