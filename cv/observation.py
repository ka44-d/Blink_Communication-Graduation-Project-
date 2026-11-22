"""Plain data passed between landmarking and measurement (no MediaPipe dependency)."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class FaceObservation:
    landmarks: np.ndarray                       # (N>=468, 3) normalized x, y, z
    blendshapes: dict[str, float] = field(default_factory=dict)
