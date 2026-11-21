"""CV configuration. Every threshold lives here; JSON overrides defaults (config/cv_config.json)."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path

log = logging.getLogger("blink.config")
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ROOT / "config" / "cv_config.json"
DEFAULT_PROFILE_PATH = ROOT / "data" / "calibration.json"
DEFAULT_MODEL_PATH = ROOT / "models" / "face_landmarker.task"


@dataclass
class CameraConfig:
    index: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30


@dataclass
class FilterConfig:
    """One Euro Filter parameters. Higher beta = less lag on fast changes (blinks)."""
    ear_min_cutoff: float = 2.0
    ear_beta: float = 12.0
    head_min_cutoff: float = 1.0
    head_beta: float = 0.05
    d_cutoff: float = 1.0


@dataclass
class HeadConfig:
    yaw_max_deg: float = 35.0
    pitch_max_deg: float = 30.0
    roll_max_deg: float = 40.0
    speed_max_dps: float = 90.0        # faster head motion -> gestures suppressed
    min_face_px: float = 60.0          # inter-ocular distance in pixels
    max_pnp_error_px: float = 12.0


@dataclass
class FusionConfig:
    use_blendshapes: bool = True
    blendshape_weight: float = 0.5     # weight of MediaPipe blink score vs EAR (0..1)
    default_bs_open: float = 0.05
    default_bs_closed: float = 0.70


@dataclass
class GestureConfig:
    close_on: float = 0.60             # normalized closure (0 open .. 1 closed) to count as closed
    close_off: float = 0.35            # hysteresis: must fall below this to count as open
    wink_min_s: float = 0.22           # one eye closed this long -> wink
    long_blink_s: float = 0.90         # both eyes closed this long -> CONFIRM
    long_blink_min_s: float = 0.70
    long_blink_max_s: float = 1.50
    progress_start_s: float = 0.30     # long-blink progress feedback begins here
    merge_grace_s: float = 0.12        # tolerated single-eye reopen inside a bilateral closure
    release_s: float = 0.06            # eyes must stay open this long to end a gesture/gap
    cooldown_s: float = 0.50           # after a gesture ends
    blink_refractory_s: float = 0.15   # after a normal blink
    rearm_open_s: float = 0.12         # both eyes open this long before a new gesture can start
    right_wink_event: str = "NEXT"     # subject's right eye
    left_wink_event: str = "PREVIOUS"  # subject's left eye
    long_blink_event: str = "CONFIRM"


@dataclass
class CalibrationConfig:
    ready_s: float = 2.0
    open_s: float = 4.0
    blink_s: float = 10.0
    min_open_samples: int = 30
    min_blinks: int = 3
    blink_ratio: float = 0.78          # EAR/open below this = blink in progress
    min_relative_gap: float = 0.25     # (open-closed)/open must exceed this
    blink_duration_multiplier: float = 3.0


@dataclass
class NetworkConfig:
    url: str = "ws://127.0.0.1:8000/ws"
    max_event_age_s: float = 1.0       # stale gestures are dropped, never fired late
    progress_interval_s: float = 0.08


@dataclass
class CVConfig:
    camera: CameraConfig = field(default_factory=CameraConfig)
    filters: FilterConfig = field(default_factory=FilterConfig)
    head: HeadConfig = field(default_factory=HeadConfig)
    fusion: FusionConfig = field(default_factory=FusionConfig)
    gesture: GestureConfig = field(default_factory=GestureConfig)
    calibration: CalibrationConfig = field(default_factory=CalibrationConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    swap_eyes: bool = False            # set True if left/right are reversed on your camera
    model_path: str = str(DEFAULT_MODEL_PATH)
    profile_path: str = str(DEFAULT_PROFILE_PATH)


def _apply(obj, data: dict, path: str = "") -> None:
    names = {f.name for f in fields(obj)}
    for key, value in data.items():
        if key not in names:
            log.warning("Unknown config key ignored: %s%s", path, key)
            continue
        cur = getattr(obj, key)
        if is_dataclass(cur) and isinstance(value, dict):
            _apply(cur, value, f"{path}{key}.")
        else:
            setattr(obj, key, type(cur)(value) if cur is not None else value)


def load_config(path: str | Path | None = None) -> CVConfig:
    cfg = CVConfig()
    p = Path(path) if path else DEFAULT_CONFIG_PATH
    if p.exists():
        _apply(cfg, json.loads(p.read_text(encoding="utf-8")))
        log.info("Loaded config from %s", p)
    elif path:
        raise FileNotFoundError(p)
    return cfg
