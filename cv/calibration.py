"""Per-user calibration: eye-open reference, natural-blink closed level, long-blink duration."""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path

import numpy as np

from .config import CalibrationConfig, GestureConfig
from .signals import Signals

log = logging.getLogger("blink.calibration")
PROFILE_VERSION = 1


class CalibrationError(Exception):
    """Raised with a user-readable reason when calibration cannot produce usable thresholds."""


@dataclass
class EyeRef:
    ear_open: float
    ear_closed: float
    bs_open: float | None = None
    bs_closed: float | None = None


@dataclass
class CalibrationProfile:
    left: EyeRef
    right: EyeRef
    blink_median_s: float = 0.2
    long_blink_s: float = 0.9
    created_at: float = field(default_factory=time.time)
    version: int = PROFILE_VERSION

    @staticmethod
    def default() -> "CalibrationProfile":
        return CalibrationProfile(EyeRef(0.30, 0.10), EyeRef(0.30, 0.10))

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        os.replace(tmp, p)

    @staticmethod
    def load(path: str | Path) -> "CalibrationProfile | None":
        p = Path(path)
        if not p.exists():
            return None
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if d.get("version") != PROFILE_VERSION:
                return None
            return CalibrationProfile(EyeRef(**d["left"]), EyeRef(**d["right"]), d["blink_median_s"],
                                      d["long_blink_s"], d["created_at"], d["version"])
        except (OSError, ValueError, KeyError, TypeError) as exc:
            log.warning("Ignoring unreadable calibration file %s: %s", p, exc)
            return None


def _robust_open(values: list[float]) -> float:
    """Median of the upper 70% of samples (excludes blinks that happened during the open phase)."""
    a = np.sort(np.asarray(values))
    return float(np.median(a[int(len(a) * 0.3):]))


class Calibrator:
    def __init__(self, cfg: CalibrationConfig, gesture_cfg: GestureConfig) -> None:
        self.cfg, self.gcfg = cfg, gesture_cfg
        self._open: list[Signals] = []
        self._blink: list[Signals] = []

    def feed_open(self, s: Signals) -> None:
        if s.valid and s.stable:
            self._open.append(s)

    def feed_blink(self, s: Signals) -> None:
        if s.valid and s.stable:
            self._blink.append(s)

    def build(self) -> CalibrationProfile:
        c = self.cfg
        if len(self._open) < c.min_open_samples:
            raise CalibrationError("Face not tracked reliably during the open-eyes phase. "
                                   "Face the camera, keep your head still and improve lighting.")
        o_l = _robust_open([s.left_ear for s in self._open])
        o_r = _robust_open([s.right_ear for s in self._open])
        bs_l = [s.left_bs for s in self._open if s.left_bs is not None]
        bs_r = [s.right_bs for s in self._open if s.right_bs is not None]
        bso_l = float(np.median(bs_l)) if bs_l else None
        bso_r = float(np.median(bs_r)) if bs_r else None

        blinks = self._segment_blinks(o_l, o_r)
        if len(blinks) < c.min_blinks:
            raise CalibrationError(f"Only {len(blinks)} natural blinks detected (need {c.min_blinks}). "
                                   "Blink normally during the blink phase and try again.")
        min_l = float(np.percentile([b["min_l"] for b in blinks], 25))
        min_r = float(np.percentile([b["min_r"] for b in blinks], 25))
        for name, o, m in (("left", o_l, min_l), ("right", o_r, min_r)):
            if (o - m) / o < c.min_relative_gap:
                raise CalibrationError(f"{name.capitalize()} eye barely changes when blinking "
                                       f"(open {o:.2f}, closed {m:.2f}). Check lighting/glasses and retry.")
        mx_l = [b["max_bl"] for b in blinks if b["max_bl"] is not None]
        mx_r = [b["max_br"] for b in blinks if b["max_br"] is not None]
        median_s = float(np.median([b["dur"] for b in blinks]))
        long_s = min(max(self.gcfg.long_blink_s, c.blink_duration_multiplier * median_s),
                     self.gcfg.long_blink_max_s)
        prof = CalibrationProfile(
            EyeRef(o_l, min_l, bso_l, float(np.median(mx_l)) if mx_l else None),
            EyeRef(o_r, min_r, bso_r, float(np.median(mx_r)) if mx_r else None),
            median_s, long_s)
        log.info("Calibration: L open=%.3f closed=%.3f | R open=%.3f closed=%.3f | %d blinks, "
                 "median %.2fs -> long blink %.2fs", o_l, min_l, o_r, min_r, len(blinks), median_s, long_s)
        return prof

    def _segment_blinks(self, o_l: float, o_r: float) -> list[dict]:
        out, cur = [], []

        def close_segment():
            if len(cur) >= 2:
                dur = cur[-1].ts - cur[0].ts + 1 / 30
                if dur <= 1.2:
                    bl = [s.left_bs for s in cur if s.left_bs is not None]
                    br = [s.right_bs for s in cur if s.right_bs is not None]
                    out.append({"dur": dur, "min_l": min(s.left_ear for s in cur),
                                "min_r": min(s.right_ear for s in cur),
                                "max_bl": max(bl) if bl else None, "max_br": max(br) if br else None})
            cur.clear()

        prev_ts = None
        for s in self._blink:
            if prev_ts is not None and s.ts - prev_ts > 0.2:
                close_segment()
            prev_ts = s.ts
            ratio = min(s.left_ear / o_l, s.right_ear / o_r)
            if ratio < self.cfg.blink_ratio:
                cur.append(s)
            else:
                close_segment()
        close_segment()
        return out


class Phase(Enum):
    READY = "ready"
    OPEN = "open"
    BLINK = "blink"
    DONE = "done"


@dataclass
class SessionStatus:
    phase: Phase
    instruction: str
    progress: float            # 0..1 within the current phase
    done: bool = False


class CalibrationSession:
    """Time-driven wizard around Calibrator. UI-agnostic: the caller renders the status."""

    TEXT = {Phase.READY: "Get ready: sit comfortably, face the camera",
            Phase.OPEN: "Look at the camera with eyes naturally open",
            Phase.BLINK: "Blink naturally (normal blinks, about once every 2-3 seconds)",
            Phase.DONE: "Calibration complete"}

    def __init__(self, cfg: CalibrationConfig, gesture_cfg: GestureConfig) -> None:
        self.cfg = cfg
        self.calibrator = Calibrator(cfg, gesture_cfg)
        self.phase = Phase.READY
        self._t0: float | None = None

    def update(self, s: Signals) -> SessionStatus:
        if self._t0 is None:
            self._t0 = s.ts
        length = {Phase.READY: self.cfg.ready_s, Phase.OPEN: self.cfg.open_s,
                  Phase.BLINK: self.cfg.blink_s}.get(self.phase, 1.0)
        if self.phase == Phase.OPEN:
            self.calibrator.feed_open(s)
        elif self.phase == Phase.BLINK:
            self.calibrator.feed_blink(s)
        progress = min((s.ts - self._t0) / length, 1.0)
        if progress >= 1.0 and self.phase != Phase.DONE:
            self.phase = {Phase.READY: Phase.OPEN, Phase.OPEN: Phase.BLINK, Phase.BLINK: Phase.DONE}[self.phase]
            self._t0 = s.ts
            progress = 0.0
        return SessionStatus(self.phase, self.TEXT[self.phase], progress, self.phase == Phase.DONE)

    def result(self) -> CalibrationProfile:
        return self.calibrator.build()
