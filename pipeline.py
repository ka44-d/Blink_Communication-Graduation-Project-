"""Frame pipeline: FaceObservation -> signals -> normalized closure -> state machine -> events."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

from .calibration import CalibrationProfile, EyeRef
from .config import CVConfig
from .events import GestureEvent, NormalBlink, ProgressEvent
from .observation import FaceObservation
from .signals import SignalExtractor, Signals
from .state_machine import GestureState, GestureStateMachine, Observation

log = logging.getLogger("blink.pipeline")


def closure(ref: EyeRef, ear: float, bs: float | None, cfg: CVConfig) -> float:
    """Normalize to 0 (open) .. 1 (closed), fusing EAR with the MediaPipe blink blendshape."""
    ear_c = (ref.ear_open - ear) / max(ref.ear_open - ref.ear_closed, 1e-3)
    ear_c = float(np.clip(ear_c, 0.0, 1.0))
    if bs is None:
        return ear_c
    f = cfg.fusion
    b_open = ref.bs_open if ref.bs_open is not None else f.default_bs_open
    b_closed = ref.bs_closed if ref.bs_closed is not None else f.default_bs_closed
    if b_closed - b_open < 0.2:                 # degenerate blendshape calibration: trust EAR only
        return ear_c
    bs_c = float(np.clip((bs - b_open) / (b_closed - b_open), 0.0, 1.0))
    return f.blendshape_weight * bs_c + (1 - f.blendshape_weight) * ear_c


@dataclass
class FrameResult:
    signals: Signals
    left_closure: float = 0.0
    right_closure: float = 0.0
    state: GestureState = GestureState.IDLE
    emissions: list[GestureEvent | ProgressEvent | NormalBlink] = field(default_factory=list)

    @property
    def gestures(self) -> list[GestureEvent]:
        return [e for e in self.emissions if isinstance(e, GestureEvent)]


class GesturePipeline:
    def __init__(self, cfg: CVConfig, profile: CalibrationProfile | None = None) -> None:
        self.cfg = cfg
        self.profile = profile or CalibrationProfile.default()
        self.extractor = SignalExtractor(cfg)
        self.machine = GestureStateMachine(cfg.gesture, self.profile.long_blink_s)

    def process(self, face: FaceObservation | None, wh: tuple[int, int], ts: float) -> FrameResult:
        sig = self.extractor.process(face, wh, ts)
        lc = rc = 0.0
        if sig.valid:
            lc = closure(self.profile.left, sig.left_ear, sig.left_bs, self.cfg)
            rc = closure(self.profile.right, sig.right_ear, sig.right_bs, self.cfg)
        present = sig.valid
        emissions = self.machine.update(Observation(ts, present, lc, rc, sig.stable))
        for e in emissions:
            if isinstance(e, GestureEvent):
                log.info("GESTURE %s -> %s (conf %.2f, %.2fs)", e.gesture, e.event, e.confidence, e.duration_s)
            elif isinstance(e, NormalBlink):
                log.debug("normal blink %.2fs (ignored)", e.duration_s)
        return FrameResult(sig, lc, rc, self.machine.state, emissions)
