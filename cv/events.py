"""Events produced by the CV pipeline (CV -> communication layer)."""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class GestureEvent:
    event: str          # NEXT | PREVIOUS | CONFIRM
    gesture: str        # right_wink | left_wink | long_blink
    ts: float           # monotonic seconds
    confidence: float
    duration_s: float

    def to_message(self) -> dict:
        return {"type": "gesture", "event": self.event, "source": "cv", "ts": time.time(),
                "confidence": round(self.confidence, 3),
                "debug": {"gesture": self.gesture, "duration_s": round(self.duration_s, 3)}}


@dataclass(frozen=True)
class ProgressEvent:
    """Long-blink confirmation progress 0..1 (0 = cancelled/finished)."""
    value: float
    ts: float

    def to_message(self) -> dict:
        return {"type": "progress", "value": round(self.value, 3), "source": "cv", "ts": time.time()}


@dataclass(frozen=True)
class NormalBlink:
    """A normal blink. Logged only: it never produces a UI command."""
    ts: float
    duration_s: float
