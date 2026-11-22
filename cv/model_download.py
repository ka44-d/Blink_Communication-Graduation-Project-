"""Download the official MediaPipe Face Landmarker model (one-time, needs internet)."""
from __future__ import annotations

import logging
import urllib.request
from pathlib import Path

log = logging.getLogger("blink.model")
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/face_landmarker/"
             "face_landmarker/float16/1/face_landmarker.task")


def ensure_model(path: str | Path) -> Path:
    p = Path(path)
    if p.exists() and p.stat().st_size > 1_000_000:
        return p
    p.parent.mkdir(parents=True, exist_ok=True)
    log.info("Downloading Face Landmarker model to %s ...", p)
    tmp = p.with_suffix(".part")
    try:
        urllib.request.urlretrieve(MODEL_URL, tmp)
    except OSError as exc:
        raise RuntimeError(f"Could not download the model ({exc}). Download it manually from\n  {MODEL_URL}\n"
                           f"and save it as {p}") from exc
    tmp.replace(p)
    return p


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from .config import load_config
    print(ensure_model(load_config().model_path))
