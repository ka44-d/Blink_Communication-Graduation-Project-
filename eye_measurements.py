"""Eye openness measurements: EAR from landmarks, plus MediaPipe blink blendshapes."""
from __future__ import annotations

import numpy as np

from .landmarks import BLENDSHAPE_LEFT, BLENDSHAPE_RIGHT, LEFT_EYE, RIGHT_EYE


def eye_aspect_ratio(p: np.ndarray) -> float:
    """EAR = (|p2-p6| + |p3-p5|) / (2 |p1-p4|), p in pixel coordinates, shape (6, 2)."""
    horiz = np.linalg.norm(p[0] - p[3])
    if horiz < 1e-6:
        return 0.0
    return float((np.linalg.norm(p[1] - p[5]) + np.linalg.norm(p[2] - p[4])) / (2.0 * horiz))


def _eye_points(landmarks: np.ndarray, ids: tuple[int, ...], wh: tuple[int, int]) -> np.ndarray:
    return landmarks[list(ids), :2] * np.array(wh, dtype=np.float64)


def measure_eyes(landmarks: np.ndarray, wh: tuple[int, int], swap: bool = False):
    """Return ((left_ear, right_ear), (left_width_px, right_width_px)) for the subject's eyes."""
    left = _eye_points(landmarks, LEFT_EYE, wh)
    right = _eye_points(landmarks, RIGHT_EYE, wh)
    if swap:
        left, right = right, left
    return ((eye_aspect_ratio(left), eye_aspect_ratio(right)),
            (float(np.linalg.norm(left[0] - left[3])), float(np.linalg.norm(right[0] - right[3]))))


def blink_scores(blendshapes: dict[str, float], swap: bool = False) -> tuple[float | None, float | None]:
    l, r = blendshapes.get(BLENDSHAPE_LEFT), blendshapes.get(BLENDSHAPE_RIGHT)
    return (r, l) if swap else (l, r)
