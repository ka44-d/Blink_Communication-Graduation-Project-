"""Temporal gesture state machine. Pure logic: no camera, no I/O, fully unit-testable.

Input per frame: closure per eye (0 = open .. 1 = closed), face presence and head stability.
Never classifies from a single frame: a wink needs wink_min_s of one-eye closure, a long blink
needs long_blink_s of two-eye closure, and every gesture fires exactly once (on the way in) and
must be released + cooled down + re-armed before the next one can start.

States: IDLE -> EYE_CLOSING -> (WINK_DETECTED | EYE_CLOSED -> LONG_BLINK_DETECTED) -> COOLDOWN -> IDLE
A bilateral closure that ends early is a NORMAL blink (logged, no command). Once both eyes have
closed, the gesture can never turn into a wink (a blink whose second eye lags is not a wink).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .config import GestureConfig
from .events import GestureEvent, NormalBlink, ProgressEvent


class GestureState(Enum):
    IDLE = "IDLE"
    EYE_CLOSING = "EYE_CLOSING"
    EYE_CLOSED = "EYE_CLOSED"
    WINK_DETECTED = "WINK_DETECTED"
    LONG_BLINK_DETECTED = "LONG_BLINK_DETECTED"
    COOLDOWN = "COOLDOWN"


@dataclass(frozen=True)
class Observation:
    ts: float
    face: bool
    left: float          # closure of the subject's left eye, 0..1
    right: float
    stable: bool = True  # head still / pose in range / landmarks trustworthy


class GestureStateMachine:
    def __init__(self, cfg: GestureConfig, long_blink_s: float | None = None) -> None:
        self.cfg = cfg
        self.long_blink_s = min(max(long_blink_s or cfg.long_blink_s, cfg.long_blink_min_s), cfg.long_blink_max_s)
        self.reset()

    # ------------------------------------------------------------------ public
    def reset(self) -> None:
        self.state = GestureState.IDLE
        self._l = self._r = False
        self._armed = False
        self._open_since: float | None = None
        self._t0 = self._t_both = self._last_both = self._cool_until = 0.0
        self._eye: str | None = None
        self._gap_since = self._notboth_since = self._release_since = None
        self._sum_a = self._sum_b = 0.0
        self._n = 0
        self._progressing = False

    def update(self, o: Observation) -> list[GestureEvent | ProgressEvent | NormalBlink]:
        out: list = []
        if not o.face or not o.stable:          # missing face / unstable data: cancel, never guess
            self._on_lost(o.ts, out)
            return out
        c = self.cfg
        self._l = o.left >= c.close_on or (self._l and o.left > c.close_off)
        self._r = o.right >= c.close_on or (self._r and o.right > c.close_off)
        if not self._l and not self._r:
            self._open_since = o.ts if self._open_since is None else self._open_since
        else:
            self._open_since = None
        getattr(self, "_s_" + self.state.name.lower())(o, out)
        return out

    # ------------------------------------------------------------------ helpers
    def _open_for(self, ts: float) -> float:
        return 0.0 if self._open_since is None else ts - self._open_since

    def _end_progress(self, ts: float, out: list) -> None:
        if self._progressing:
            out.append(ProgressEvent(0.0, ts))
            self._progressing = False

    def _enter_cooldown(self, ts: float, seconds: float) -> None:
        self.state = GestureState.COOLDOWN
        self._cool_until = ts + seconds
        self._armed = False
        self._release_since = None

    def _on_lost(self, ts: float, out: list) -> None:
        self._end_progress(ts, out)
        was = self.state
        self._l = self._r = False
        self._open_since = None
        self._armed = False
        self._gap_since = self._notboth_since = self._release_since = None
        if was in (GestureState.WINK_DETECTED, GestureState.LONG_BLINK_DETECTED, GestureState.COOLDOWN):
            self._enter_cooldown(ts, self.cfg.cooldown_s)
        else:
            self.state = GestureState.IDLE

    # ------------------------------------------------------------------ states
    def _s_idle(self, o: Observation, out: list) -> None:
        if not self._armed:
            if self._open_for(o.ts) >= self.cfg.rearm_open_s:
                self._armed = True
            return
        if self._l or self._r:
            self.state = GestureState.EYE_CLOSING
            self._t0, self._gap_since = o.ts, None
            self._eye = "left" if self._l and not self._r else "right" if self._r and not self._l else "both"
            self._sum_a = self._sum_b = 0.0
            self._n = 0
            if self._l and self._r:
                self._enter_closed(o.ts)

    def _enter_closed(self, ts: float) -> None:
        self.state = GestureState.EYE_CLOSED
        self._t_both = self._last_both = ts
        self._notboth_since = None
        self._sum_a, self._n = 0.0, 0

    def _s_eye_closing(self, o: Observation, out: list) -> None:
        c = self.cfg
        if self._l and self._r:
            self._enter_closed(o.ts)
            return
        if not self._l and not self._r:          # brief reopen tolerated; sustained -> abort (noise)
            self._gap_since = self._gap_since if self._gap_since is not None else o.ts
            if o.ts - self._gap_since >= c.release_s:
                self.state, self._gap_since = GestureState.IDLE, None
            return
        self._gap_since = None
        eye = "left" if self._l else "right"
        if eye != self._eye:                     # side changed: restart timing
            self._eye, self._t0, self._sum_a, self._sum_b, self._n = eye, o.ts, 0.0, 0.0, 0
        closed, other = (o.left, o.right) if eye == "left" else (o.right, o.left)
        self._sum_a, self._sum_b, self._n = self._sum_a + closed, self._sum_b + other, self._n + 1
        dur = o.ts - self._t0
        if dur >= c.wink_min_s:
            conf = max(0.0, min(1.0, self._sum_a / self._n - self._sum_b / self._n))
            name = c.left_wink_event if eye == "left" else c.right_wink_event
            out.append(GestureEvent(name, f"{eye}_wink", o.ts, conf, dur))
            self.state, self._release_since = GestureState.WINK_DETECTED, None

    def _s_eye_closed(self, o: Observation, out: list) -> None:
        c = self.cfg
        if self._l and self._r:
            self._last_both, self._notboth_since = o.ts, None
            self._sum_a, self._n = self._sum_a + min(o.left, o.right), self._n + 1
            dur = o.ts - self._t_both
            if dur >= self.long_blink_s:
                conf = max(0.0, min(1.0, self._sum_a / self._n))
                out.append(GestureEvent(c.long_blink_event, "long_blink", o.ts, conf, dur))
                self._end_progress(o.ts, out)
                self.state, self._release_since = GestureState.LONG_BLINK_DETECTED, None
            elif dur >= c.progress_start_s:
                self._progressing = True
                out.append(ProgressEvent(min((dur - c.progress_start_s) /
                                             (self.long_blink_s - c.progress_start_s), 1.0), o.ts))
            return
        self._notboth_since = self._notboth_since if self._notboth_since is not None else o.ts
        if not self._l and not self._r and self._open_for(o.ts) >= c.release_s:
            out.append(NormalBlink(o.ts, self._last_both - self._t_both))
            self._end_progress(o.ts, out)
            self._enter_cooldown(o.ts, c.blink_refractory_s)
        elif o.ts - self._notboth_since > c.merge_grace_s:   # one eye lingering: ambiguous, ignore
            self._end_progress(o.ts, out)
            self._enter_cooldown(o.ts, c.cooldown_s)

    def _wait_release(self, o: Observation) -> None:
        if not self._l and not self._r:
            self._release_since = self._release_since if self._release_since is not None else o.ts
            if o.ts - self._release_since >= self.cfg.release_s:
                self._enter_cooldown(o.ts, self.cfg.cooldown_s)
        else:
            self._release_since = None

    def _s_wink_detected(self, o: Observation, out: list) -> None:
        self._wait_release(o)

    def _s_long_blink_detected(self, o: Observation, out: list) -> None:
        self._wait_release(o)

    def _s_cooldown(self, o: Observation, out: list) -> None:
        if o.ts >= self._cool_until and self._open_for(o.ts) >= self.cfg.rearm_open_s:
            self.state, self._armed = GestureState.IDLE, True
