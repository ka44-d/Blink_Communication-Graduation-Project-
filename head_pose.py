"""Head pose (yaw/pitch/roll) from 6 landmarks with OpenCV solvePnP."""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .landmarks import HEAD_POSE_IDS

# Generic face model in mm. Camera-style axes: x right, y down, z away from camera.
# 'x<0' is the image-left side, i.e. the subject's RIGHT (landmarks 33, 61).
MODEL_POINTS: dict[int, tuple[float, float, float]] = {
    1: (0.0, 0.0, 0.0), 152: (0.0, 63.0, 12.0),
    33: (-43.0, -33.0, 26.0), 263: (43.0, -33.0, 26.0),
    61: (-28.0, 30.0, 20.0), 291: (28.0, 30.0, 20.0),
}


@dataclass(frozen=True)
class HeadPose:
    yaw: float
    pitch: float
    roll: float


def camera_matrix(img_wh: tuple[int, int]) -> np.ndarray:
    w, h = img_wh
    return np.array([[w, 0, w / 2], [0, w, h / 2], [0, 0, 1]], dtype=np.float64)


def euler_from_rvec(rvec: np.ndarray) -> HeadPose:
    rot, _ = cv2.Rodrigues(np.asarray(rvec, dtype=np.float64))
    ang = cv2.RQDecomp3x3(rot)[0]
    return HeadPose(yaw=float(ang[1]), pitch=float(ang[0]), roll=float(ang[2]))


class HeadPoseEstimator:
    """Stateful: reuses the previous solution as initial guess for temporal stability."""

    def __init__(self, max_error_px: float = 12.0) -> None:
        self.max_error_px = max_error_px
        self._obj = np.array([MODEL_POINTS[i] for i in HEAD_POSE_IDS], dtype=np.float64)
        self.reset()

    def reset(self) -> None:
        self._rvec: np.ndarray | None = None
        self._tvec: np.ndarray | None = None

    def estimate(self, landmarks: np.ndarray, img_wh: tuple[int, int]) -> HeadPose | None:
        w, h = img_wh
        img = np.array([[landmarks[i, 0] * w, landmarks[i, 1] * h] for i in HEAD_POSE_IDS], dtype=np.float64)
        cam = camera_matrix(img_wh)
        try:
            if self._rvec is None:
                ok, rvec, tvec = cv2.solvePnP(self._obj, img, cam, None, flags=cv2.SOLVEPNP_ITERATIVE)
            else:
                ok, rvec, tvec = cv2.solvePnP(self._obj, img, cam, None, self._rvec.copy(),
                                              self._tvec.copy(), True, flags=cv2.SOLVEPNP_ITERATIVE)
        except cv2.error:
            ok = False
        if not ok or tvec[2, 0] <= 0:
            self.reset()
            return None
        proj, _ = cv2.projectPoints(self._obj, rvec, tvec, cam, None)
        err = float(np.mean(np.linalg.norm(proj.reshape(-1, 2) - img, axis=1)))
        if err > self.max_error_px:
            self.reset()
            return None
        self._rvec, self._tvec = rvec, tvec
        return euler_from_rvec(rvec)
