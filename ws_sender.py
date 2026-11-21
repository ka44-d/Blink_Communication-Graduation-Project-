"""Non-blocking WebSocket sender with auto-reconnect. Runs in its own thread so a slow or
absent server can never stall frame processing."""
from __future__ import annotations

import json
import logging
import queue
import threading
import time

from websockets.sync.client import connect

from .events import GestureEvent, ProgressEvent

log = logging.getLogger("blink.ws")


class GestureSender:
    def __init__(self, url: str, max_event_age_s: float = 1.0, progress_interval_s: float = 0.08) -> None:
        self.url, self.max_age, self.progress_interval = url, max_event_age_s, progress_interval_s
        self._q: queue.Queue = queue.Queue(maxsize=256)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="ws-sender", daemon=True)
        self.connected = False
        self._last_progress = 0.0
        self._last_status: tuple | None = None
        self._last_status_t = 0.0

    def start(self) -> None:
        self._thread.start()

    def stop(self, flush_timeout: float = 1.0) -> None:
        """Stop the thread, first giving already-queued events a moment to be delivered."""
        end = time.monotonic() + flush_timeout
        while self.connected and not self._q.empty() and time.monotonic() < end:
            time.sleep(0.02)
        self._stop.set()
        self._thread.join(timeout=2)

    # --- producers (called from the CV loop; never block) ---
    def _put(self, kind: str, msg: dict) -> None:
        try:
            self._q.put_nowait((kind, time.monotonic(), msg))
        except queue.Full:
            log.warning("Send queue full; dropping %s", kind)

    def send_gesture(self, e: GestureEvent) -> None:
        self._put("gesture", e.to_message())

    def send_progress(self, e: ProgressEvent) -> None:
        now = time.monotonic()
        if e.value in (0.0, 1.0) or now - self._last_progress >= self.progress_interval:
            self._last_progress = now
            self._put("progress", e.to_message())

    def send_status(self, face: bool, state: str, calibrated: bool) -> None:
        key, now = (face, state, calibrated), time.monotonic()
        if key != self._last_status or now - self._last_status_t > 1.0:
            self._last_status, self._last_status_t = key, now
            self._put("status", {"type": "status", "source": "cv", "face": face, "state": state,
                                 "calibrated": calibrated, "ts": time.time()})

    # --- consumer thread ---
    def _run(self) -> None:
        backoff = 0.5
        while not self._stop.is_set():
            try:
                with connect(self.url, open_timeout=2) as ws:
                    self.connected, backoff = True, 0.5
                    log.info("Connected to %s", self.url)
                    while not self._stop.is_set():
                        try:
                            kind, t, msg = self._q.get(timeout=0.25)
                        except queue.Empty:
                            continue
                        if kind != "status" and time.monotonic() - t > self.max_age:
                            log.warning("Dropped stale %s event (%.1fs old)", kind, time.monotonic() - t)
                            continue
                        ws.send(json.dumps(msg, ensure_ascii=False))
            except Exception as exc:                    # noqa: BLE001 - reconnect on any failure
                if self.connected:
                    log.warning("WebSocket lost: %s", exc)
                self.connected = False
                self._stop.wait(backoff)
                backoff = min(backoff * 2, 5.0)
        self.connected = False
