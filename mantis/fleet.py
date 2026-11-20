"""Fleet — a roster of YOUR OWN devices running MANTIS.

Each device you own runs ``mantis agent --hub <url>`` with a shared fleet key and
periodically reports its OWN telemetry (hostname, platform, level, posture grade,
battery, uptime) to a hub MANTIS. The hub shows them all on one dashboard.

This is consensual, opt-in monitoring of gear you control — devices only ever
report about *themselves*. There is no remote control, no file access, no
scanning of anyone else's devices, and no way to pull data off a device that
isn't running the agent with your key. That boundary is deliberate.
"""

from __future__ import annotations

import json
import os
import platform
import socket
import time
import uuid
from typing import Any, Dict, List, Optional

FLEET_FILE = "fleet.json"
_START = time.time()


# --------------------------------------------------------------------------- #
# Hub-side roster storage
# --------------------------------------------------------------------------- #
def _path(home: str) -> str:
    return os.path.join(home, FLEET_FILE)


def _load(home: str) -> Dict[str, Any]:
    try:
        with open(_path(home), "r", encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save(home: str, data: Dict[str, Any]) -> None:
    os.makedirs(home, exist_ok=True)
    tmp = _path(home) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    os.replace(tmp, _path(home))


def record(home: str, device: Dict[str, Any]) -> None:
    """Store/refresh one device's self-report on the hub."""
    data = _load(home)
    did = str(device.get("id") or device.get("name") or "unknown")
    entry = {k: device.get(k) for k in (
        "id", "name", "platform", "version", "level", "rank",
        "posture_grade", "posture_score", "battery", "uptime_s",
        "ip", "mood", "stage") if k in device}
    entry["last_seen"] = time.time()
    data[did] = entry
    data = {k: v for k, v in data.items() if time.time() - v.get("last_seen", 0) < 7 * 86400}
    _save(home, data)


def roster(home: str, stale_s: int = 180) -> List[Dict[str, Any]]:
    data = _load(home)
    now = time.time()
    out = []
    for v in data.values():
        v = dict(v)
        v["online"] = (now - v.get("last_seen", 0)) < stale_s
        v["ago"] = int(now - v.get("last_seen", 0))
        out.append(v)
    return sorted(out, key=lambda d: (not d["online"], d.get("name", "")))


def forget(home: str, device_id: str) -> bool:
    data = _load(home)
    if device_id in data:
        del data[device_id]
        _save(home, data)
        return True
    return False


# --------------------------------------------------------------------------- #
# Device-side self report
# --------------------------------------------------------------------------- #
def _device_id(home: str) -> str:
    """Stable per-install id (persisted in home/device_id)."""
    p = os.path.join(home, "device_id")
    try:
        if os.path.exists(p):
            return open(p).read().strip()
        did = socket.gethostname() + "-" + uuid.uuid4().hex[:6]
        with open(p, "w") as fh:
            fh.write(did)
        return did
    except Exception:
        return socket.gethostname()


def _uptime_s() -> int:
    try:
        with open("/proc/uptime") as fh:
            return int(float(fh.read().split()[0]))
    except Exception:
        return int(time.time() - _START)


def _local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def gather_self(engine) -> Dict[str, Any]:
    from . import __version__
    snap = engine.snapshot()
    p = snap.get("posture", {}) or {}
    batt = None
    try:
        from .power import read_battery
        b = read_battery(engine.home)
        batt = int(b["percent"]) if b else None
    except Exception:
        pass
    return {
        "id": _device_id(engine.home),
        "name": socket.gethostname(),
        "platform": f"{platform.system()} {platform.machine()}",
        "version": __version__,
        "level": snap.get("level"),
        "rank": snap.get("rank"),
        "posture_grade": p.get("grade"),
        "posture_score": p.get("score"),
        "battery": batt,
        "uptime_s": _uptime_s(),
        "ip": _local_ip(),
        "mood": snap.get("mood"),
        "stage": (snap.get("stage") or {}).get("label"),
    }


def fmt_uptime(s: int) -> str:
    s = int(s or 0)
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, _ = divmod(s, 60)
    if d:
        return f"{d}d{h}h"
    if h:
        return f"{h}h{m}m"
    return f"{m}m"
