"""Optional OpenCV debug window. ASCII text only (cv2 cannot draw Arabic)."""
from __future__ import annotations

import cv2
import numpy as np

from .calibration import SessionStatus
from .pipeline import FrameResult

GREEN, YELLOW, RED, WHITE = (80, 220, 120), (60, 210, 255), (60, 60, 240), (240, 240, 240)
WINDOW = "Blink CV (q = quit)"


def _bar(img, x, y, w, value, label, color):
    cv2.rectangle(img, (x, y), (x + w, y + 14), (60, 60, 60), 1)
    cv2.rectangle(img, (x, y), (x + int(w * float(np.clip(value, 0, 1))), y + 14), color, -1)
    cv2.putText(img, label, (x + w + 8, y + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, WHITE, 1)


def show_run(frame: np.ndarray, r: FrameResult, last_gesture: str, fps: float) -> bool:
    img = cv2.flip(frame, 1)       # display only; processing uses the unflipped frame
    s = r.signals
    cv2.putText(img, f"state: {r.state.value}", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, YELLOW, 2)
    cv2.putText(img, f"{s.reason}  fps {fps:.0f}", (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                GREEN if s.stable else RED, 1)
    # Mirrored view: subject's RIGHT eye appears on the screen's right, like a mirror.
    _bar(img, 10, 62, 120, r.right_closure, f"R closure {r.right_closure:.2f} (EAR {s.right_ear:.2f})", WHITE)
    _bar(img, 10, 82, 120, r.left_closure, f"L closure {r.left_closure:.2f} (EAR {s.left_ear:.2f})", WHITE)
    cv2.putText(img, f"yaw {s.yaw:+.0f} pitch {s.pitch:+.0f} roll {s.roll:+.0f} speed {s.head_speed:.0f}",
                (10, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.45, WHITE, 1)
    cv2.putText(img, f"last: {last_gesture}", (10, img.shape[0] - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.8, GREEN, 2)
    cv2.imshow(WINDOW, img)
    return (cv2.waitKey(1) & 0xFF) not in (ord("q"), 27)


def show_calibration(frame: np.ndarray, st: SessionStatus, sig_reason: str) -> bool:
    img = cv2.flip(frame, 1)
    h, w = img.shape[:2]
    cv2.rectangle(img, (0, 0), (w, 70), (0, 0, 0), -1)
    cv2.putText(img, f"CALIBRATION - {st.phase.value.upper()}", (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, YELLOW, 2)
    cv2.putText(img, st.instruction, (10, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.55, WHITE, 1)
    _bar(img, 10, h - 30, w - 120, st.progress, f"{int(st.progress * 100)}%", GREEN)
    if sig_reason != "ok":
        cv2.putText(img, f"tracking: {sig_reason}", (10, h - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, RED, 1)
    cv2.imshow(WINDOW, img)
    return (cv2.waitKey(1) & 0xFF) not in (ord("q"), 27)
