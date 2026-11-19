"""Battery / power sensing for the handheld.

Reads battery percentage (and charging state) from whatever source the build
has, trying in order:

  1. MANTIS_BATTERY env var        -> a fixed percent (testing / manual)
  2. MANTIS_BATTERY_CMD env var    -> a shell command printing a number
  3. ~/.mantis/battery  file       -> a number written by any script
  4. PiSugar 2/3 socket server (127.0.0.1:8423)
  5. nothing -> returns None (the UI simply hides the battery indicator)

Everything is wrapped so a missing source never raises; the pet runs the same
with or without a battery.
"""

from __future__ import annotations

import os
import socket
import subprocess
from typing import Dict, Optional


def _from_env() -> Optional[Dict]:
    v = os.environ.get("MANTIS_BATTERY") or os.environ.get("PSYCHOMANTIS_BATTERY")
    if v is None:
        return None
    try:
        return {"percent": max(0.0, min(100.0, float(v))), "charging": False,
                "source": "env"}
    except ValueError:
        return None


def _from_cmd() -> Optional[Dict]:
    cmd = os.environ.get("MANTIS_BATTERY_CMD") or os.environ.get("PSYCHOMANTIS_BATTERY_CMD")
    if not cmd:
        return None
    try:
        out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=4)
        return {"percent": max(0.0, min(100.0, float(out.stdout.strip()))),
                "charging": False, "source": "cmd"}
    except Exception:
        return None


def _from_file(home: Optional[str]) -> Optional[Dict]:
    path = os.path.join(home or os.path.join(os.path.expanduser("~"), ".mantis"),
                        "battery")
    try:
        with open(path) as fh:
            return {"percent": max(0.0, min(100.0, float(fh.read().strip()))),
                    "charging": False, "source": "file"}
    except Exception:
        return None


def _from_pisugar() -> Optional[Dict]:
    try:
        s = socket.create_connection(("127.0.0.1", 8423), timeout=1.0)
        s.sendall(b"get battery\n")
        pct = float(s.recv(128).decode().split(":")[-1].strip())
        charging = False
        try:
            s.sendall(b"get battery_charging\n")
            charging = "true" in s.recv(128).decode().lower()
        except Exception:
            pass
        s.close()
        return {"percent": max(0.0, min(100.0, pct)), "charging": charging,
                "source": "pisugar"}
    except Exception:
        return None


def _config_battery(home: Optional[str]) -> Optional[Dict]:
    """Use the [battery] source chosen in config.toml, if any."""
    if not home:
        return None
    try:
        from . import config as CFG
        bat = (CFG.load(home) or {}).get("battery", {})
    except Exception:
        return None
    source = (bat.get("source") or "auto").lower()
    if source == "none":
        return {"__disabled__": True}       # explicitly no battery
    if source == "pisugar":
        return _from_pisugar()
    if source == "file":
        return _from_file(home)
    if source == "command":
        cmd = bat.get("command")
        if cmd:
            os.environ.setdefault("MANTIS_BATTERY_CMD", cmd)
        return _from_cmd()
    return None                              # "auto" / unset -> fall through


def read_battery(home: Optional[str] = None) -> Optional[Dict]:
    # env always wins (handy for testing)
    for fn in (_from_env, _from_cmd):
        try:
            res = fn()
        except Exception:
            res = None
        if res is not None:
            return res
    # then whatever config.toml [battery] selects
    cfg = _config_battery(home)
    if cfg is not None:
        return None if cfg.get("__disabled__") else cfg
    # then auto-detect
    for fn in (lambda: _from_file(home), _from_pisugar):
        try:
            res = fn()
        except Exception:
            res = None
        if res is not None:
            return res
    return None
