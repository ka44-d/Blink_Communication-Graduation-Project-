"""CV application loop: camera -> landmarks -> pipeline -> WebSocket. Also calibration + diagnose."""
from __future__ import annotations

import csv
import logging
import time
from dataclasses import dataclass
from pathlib import Path

import cv2

from .calibration import CalibrationError, CalibrationProfile, CalibrationSession
from .capture import WebcamCapture
from .config import CVConfig
from .events import GestureEvent, NormalBlink, ProgressEvent
from .face_landmarker import FaceLandmarkerWrapper
from .model_download import ensure_model
from .pipeline import GesturePipeline
from .preview import show_calibration, show_run
from .signals import SignalExtractor

log = logging.getLogger("blink.app")


class _Display:
    """Shows preview windows if possible; silently degrades to console-only without a display."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def show(self, fn, *args) -> bool:
        """Returns False only when the user asked to quit."""
        if not self.enabled:
            return True
        try:
            return fn(*args)
        except cv2.error as exc:
            log.warning("Preview window unavailable (%s); continuing without it.", str(exc).splitlines()[0])
            self.enabled = False
            return True


@dataclass
class RunOptions:
    preview: bool = False
    send: bool = True              # False = diagnose mode (no WebSocket)
    force_calibration: bool = False
    calibrate_only: bool = False
    signal_log: str | None = None  # CSV of numeric signals only (never images)


def run_calibration(cfg: CVConfig, cam: WebcamCapture, lm: FaceLandmarkerWrapper, window: bool = True) -> CalibrationProfile | None:
    """Interactive calibration. Returns the saved profile, or None if aborted/failed."""
    display = _Display(window)
    extractor = SignalExtractor(cfg)
    session = CalibrationSession(cfg.calibration, cfg.gesture)
    last_phase = None
    log.info("Calibration started. Follow the instructions on screen (press q to abort).")
    for frame, ts in cam.frames():
        h, w = frame.shape[:2]
        sig = extractor.process(lm.detect(frame, ts), (w, h), ts)
        st = session.update(sig)
        if st.phase != last_phase:
            log.info("[calibration] %s", st.instruction)
            last_phase = st.phase
        if not display.show(show_calibration, frame, st, sig.reason):
            log.warning("Calibration aborted.")
            return None
        if st.done:
            break
    try:
        profile = session.result()
    except CalibrationError as exc:
        log.error("Calibration failed: %s", exc)
        return None
    profile.save(cfg.profile_path)
    log.info("Calibration saved to %s", cfg.profile_path)
    return profile


def run(cfg: CVConfig, opts: RunOptions) -> int:
    model = ensure_model(cfg.model_path)
    profile = None if opts.force_calibration else CalibrationProfile.load(cfg.profile_path)
    sender = None
    csv_file = None
    display = _Display(opts.preview or not opts.send)
    try:
        with WebcamCapture(cfg.camera) as cam:
            lm = FaceLandmarkerWrapper(str(model))
            try:
                if profile is None:
                    log.info("No calibration found - starting calibration.")
                    profile = run_calibration(cfg, cam, lm, window=True)
                    if profile is None:
                        return 2
                    if opts.calibrate_only:
                        return 0
                elif opts.calibrate_only:
                    return 0
                pipeline = GesturePipeline(cfg, profile)
                if opts.send:
                    from .ws_sender import GestureSender
                    sender = GestureSender(cfg.network.url, cfg.network.max_event_age_s,
                                           cfg.network.progress_interval_s)
                    sender.start()
                writer = None
                if opts.signal_log:
                    Path(opts.signal_log).parent.mkdir(parents=True, exist_ok=True)
                    csv_file = open(opts.signal_log, "w", newline="", encoding="utf-8")
                    writer = csv.writer(csv_file)
                    writer.writerow(["ts", "reason", "l_ear", "r_ear", "l_closure", "r_closure",
                                     "yaw", "pitch", "roll", "state", "event"])
                log.info("Running. Right-eye wink=NEXT, left-eye wink=PREVIOUS, long blink=CONFIRM%s",
                         "" if opts.send else "  [DIAGNOSE: events are not sent]")
                last, fps, t_fps, n, t_diag = "-", 0.0, time.monotonic(), 0, 0.0
                for frame, ts in cam.frames():
                    h, w = frame.shape[:2]
                    r = pipeline.process(lm.detect(frame, ts), (w, h), ts)
                    for e in r.emissions:
                        if isinstance(e, GestureEvent):
                            last = f"{e.event} ({e.gesture})"
                            if sender:
                                sender.send_gesture(e)
                        elif isinstance(e, ProgressEvent) and sender:
                            sender.send_progress(e)
                        elif isinstance(e, NormalBlink):
                            last = "normal blink (ignored)"
                    if sender:
                        sender.send_status(r.signals.valid, r.state.value, True)
                    if writer:
                        s = r.signals
                        writer.writerow([f"{ts:.3f}", s.reason, f"{s.left_ear:.4f}", f"{s.right_ear:.4f}",
                                         f"{r.left_closure:.3f}", f"{r.right_closure:.3f}", f"{s.yaw:.1f}",
                                         f"{s.pitch:.1f}", f"{s.roll:.1f}", r.state.value,
                                         r.gestures[0].event if r.gestures else ""])
                    n += 1
                    if ts - t_fps >= 1.0:
                        fps, n, t_fps = n / (ts - t_fps), 0, ts
                    if not opts.send and ts - t_diag >= 0.5:
                        t_diag = ts
                        s = r.signals
                        log.info("%-20s %-12s L %.2f/%.2f R %.2f/%.2f yaw %+4.0f fps %.0f", r.state.value,
                                 s.reason, s.left_ear, r.left_closure, s.right_ear, r.right_closure, s.yaw, fps)
                    if not display.show(show_run, frame, r, last, fps):
                        break
            finally:
                lm.close()
    except KeyboardInterrupt:
        log.info("Stopped by user.")
    finally:
        if sender:
            sender.stop()
        if csv_file:
            csv_file.close()
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass
    return 0
