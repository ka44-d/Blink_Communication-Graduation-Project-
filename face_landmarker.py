"""MediaPipe Face Landmarker wrapper (Tasks API, VIDEO mode, blendshapes on)."""
from __future__ import annotations

import logging

import cv2
import numpy as np

from .observation import FaceObservation

log = logging.getLogger("blink.landmarker")


class FaceLandmarkerWrapper:
    def __init__(self, model_path: str, min_confidence: float = 0.5) -> None:
        import mediapipe as mp                                  # lazy: tests don't need it
        from mediapipe.tasks.python import BaseOptions, vision
        self._mp = mp
        opts = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO, num_faces=1, output_face_blendshapes=True,
            min_face_detection_confidence=min_confidence, min_face_presence_confidence=min_confidence,
            min_tracking_confidence=min_confidence)
        self._lm = vision.FaceLandmarker.create_from_options(opts)
        self._last_ms = -1

    def detect(self, frame_bgr: np.ndarray, ts_s: float) -> FaceObservation | None:
        """Return the (single) face or None. Timestamps are forced strictly increasing (MediaPipe rule)."""
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        ms = max(int(ts_s * 1000), self._last_ms + 1)
        self._last_ms = ms
        res = self._lm.detect_for_video(self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb), ms)
        if not res.face_landmarks:
            return None
        pts = np.array([[p.x, p.y, p.z] for p in res.face_landmarks[0]], dtype=np.float64)
        bs = {c.category_name: float(c.score) for c in res.face_blendshapes[0]} if res.face_blendshapes else {}
        return FaceObservation(pts, bs)

    def close(self) -> None:
        self._lm.close()
