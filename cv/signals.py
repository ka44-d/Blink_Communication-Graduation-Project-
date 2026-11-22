"""Landmarks -> smoothed, head-pose-compensated eye signals + head stability flag."""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass

from .config import CVConfig
from .eye_measurements import blink_scores, measure_eyes
from .head_pose import HeadPose, HeadPoseEstimator
from .landmarks import HEAD_POSE_IDS
from .observation import FaceObservation
from .one_euro import OneEuroFilter

log = logging.getLogger("blink.signals")
RESET_GAP_S = 0.3        # a gap longer than this flushes filters (stale history)
MAX_WIDTH_JUMP = 0.35    # frame-to-frame eye-width change that marks landmarks as unstable


@dataclass
class Signals:
    ts: float
    valid: bool = False             # measurements trustworthy this frame
    stable: bool = False            # valid AND head pose within limits and not moving fast
    reason: str = "no_face"
    left_ear: float = 0.0           # smoothed + yaw-compensated
    right_ear: float = 0.0
    left_bs: float | None = None    # smoothed MediaPipe blink blendshape
    right_bs: float | None = None
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    head_speed: float = 0.0         # deg/s


class SignalExtractor:
    def __init__(self, cfg: CVConfig) -> None:
        self.cfg = cfg
        f = cfg.filters
        mk = lambda c, b: OneEuroFilter(c, b, f.d_cutoff)  # noqa: E731
        self._ear = {k: mk(f.ear_min_cutoff, f.ear_beta) for k in ("l", "r")}
        self._bs = {k: mk(f.ear_min_cutoff, f.ear_beta) for k in ("l", "r")}
        self._head = {k: mk(f.head_min_cutoff, f.head_beta) for k in ("yaw", "pitch", "roll")}
        self._pose = HeadPoseEstimator(cfg.head.max_pnp_error_px)
        self._last_ts: float | None = None
        self._last_pose: HeadPose | None = None
        self._last_widths: tuple[float, float] | None = None
        self._last_ts_pose = 0.0

    def reset(self) -> None:
        for d in (self._ear, self._bs, self._head):
            for flt in d.values():
                flt.reset()
        self._pose.reset()
        self._last_pose = None
        self._last_widths = None

    def process(self, face: FaceObservation | None, wh: tuple[int, int], ts: float) -> Signals:
        if self._last_ts is not None and ts - self._last_ts > RESET_GAP_S:
            self.reset()
        self._last_ts = ts
        if face is None:
            self.reset()
            return Signals(ts, reason="no_face")
        lm, hc = face.landmarks, self.cfg.head
        pose = self._pose.estimate(lm, wh)
        if pose is None:
            return Signals(ts, reason="pose_failed")
        yaw = self._head["yaw"](pose.yaw, ts)
        pitch = self._head["pitch"](pose.pitch, ts)
        roll = self._head["roll"](pose.roll, ts)
        speed = 0.0
        if self._last_pose is not None:
            dt = max(ts - self._last_ts_pose, 1e-3)
            speed = max(abs(yaw - self._last_pose.yaw), abs(pitch - self._last_pose.pitch),
                        abs(roll - self._last_pose.roll)) / dt
        self._last_pose, self._last_ts_pose = HeadPose(yaw, pitch, roll), ts

        (l_ear, r_ear), widths = measure_eyes(lm, wh, self.cfg.swap_eyes)
        iod = math.hypot((lm[HEAD_POSE_IDS[2], 0] - lm[HEAD_POSE_IDS[3], 0]) * wh[0],
                         (lm[HEAD_POSE_IDS[2], 1] - lm[HEAD_POSE_IDS[3], 1]) * wh[1])
        sig = Signals(ts, yaw=yaw, pitch=pitch, roll=roll, head_speed=speed)

        reason = None
        if iod < hc.min_face_px:
            reason = "face_too_small"
        elif min(widths) < 4.0 or not (0.0 <= l_ear <= 0.8 and 0.0 <= r_ear <= 0.8):
            reason = "bad_landmarks"
        elif self._last_widths and any(abs(w / max(p, 1e-6) - 1) > MAX_WIDTH_JUMP
                                       for w, p in zip(widths, self._last_widths)):
            reason = "landmark_jump"
        self._last_widths = widths
        if reason:
            sig.reason = reason
            return sig

        # Yaw foreshortens eye width (EAR grows by ~1/cos(yaw)); undo it, clamped.
        comp = max(math.cos(math.radians(yaw)), 0.6)
        sig.left_ear = self._ear["l"](l_ear * comp, ts)
        sig.right_ear = self._ear["r"](r_ear * comp, ts)
        bl, br = blink_scores(face.blendshapes, self.cfg.swap_eyes)
        if bl is not None and br is not None and self.cfg.fusion.use_blendshapes:
            sig.left_bs, sig.right_bs = self._bs["l"](bl, ts), self._bs["r"](br, ts)
        sig.valid = True
        if abs(yaw) > hc.yaw_max_deg or abs(pitch) > hc.pitch_max_deg or abs(roll) > hc.roll_max_deg:
            sig.reason = "head_pose_out_of_range"
        elif speed > hc.speed_max_dps:
            sig.reason = "head_moving"
        else:
            sig.stable, sig.reason = True, "ok"
        return sig
