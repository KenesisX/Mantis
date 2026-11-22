"""Persistent configuration — ~/.mantis/config.toml.

Lets every runtime flag (eink interval, button pins, battery thresholds,
slideshow, splash, web host/port, ...) be set once in a file instead of on the
command line each run. Precedence, lowest to highest:

    built-in defaults  <  config.toml  <  environment vars  <  CLI flags

Uses the stdlib ``tomllib`` on Python 3.11+, and a small built-in parser for the
subset we use on 3.8-3.10 (so there is still zero third-party dependency).
"""

from __future__ import annotations

import os
from typing import Any, Dict

CONFIG_NAME = "config.toml"

DEFAULT_TOML = """\
# MANTIS configuration  (~/.mantis/config.toml)
# Edit and save; values here are used unless overridden by an env var or a CLI flag.

[eink]
interval = 30            # seconds between full status refreshes
rotate = 0               # 0, 90, 180 or 270
driver = "auto"          # auto | waveshare | inky
buttons = true           # enable GPIO buttons
animate = true           # idle float "bob" animation
splash = true            # show the MANTIS boot splash
slideshow = true         # calm pet flips through its unlocked stage cards
slideshow_interval = 25  # seconds between idle stage cards
low_battery = 20         # <= this %  -> low-power mode (slow, no animation)
sleep_below = 6          # <= this %  -> hibernate (deep sleep the panel)
poweroff_combo = true    # hold cast+pet to safely power off the handheld
poweroff_hold = 3        # seconds to hold before shutdown

[buttons]                # GPIO pins (BCM numbering)
feed = 5
meditate = 6
pet = 16
cast = 24
deed = 26

[web]
host = "127.0.0.1"
port = 8777
theme = "red"            # red | mono (black & white) | green | amber

[fleet]
key = ""                 # shared secret; devices with this key may report to this hub

[battery]
source = "auto"          # auto | none | pisugar | file | command
command = ""             # shell command printing a 0-100 number (for source=command)
"""


def _fmt(x) -> str:
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, (int, float)):
        return str(x)
    return '"' + str(x).replace('"', "'") + '"'


def build_toml(eink: Dict[str, Any], buttons: Dict[str, Any],
               web: Dict[str, Any], battery: Dict[str, Any],
               fleet: Dict[str, Any] = None) -> str:
    lines = ["# MANTIS configuration  (~/.mantis/config.toml)",
             "# Written by 'mantis setup'. Edit freely; CLI flags override these.", "",
             "[eink]"]
    for k in ("interval", "rotate", "driver", "buttons", "animate", "splash",
              "slideshow", "slideshow_interval", "low_battery", "sleep_below",
              "poweroff_combo", "poweroff_hold"):
        if k in eink:
            lines.append(f"{k} = {_fmt(eink[k])}")
    lines += ["", "[buttons]"]
    for k in ("feed", "meditate", "pet", "cast", "deed"):
        if k in buttons:
            lines.append(f"{k} = {_fmt(buttons[k])}")
    lines += ["", "[web]"]
    for k in ("host", "port", "theme"):
        if k in web:
            lines.append(f"{k} = {_fmt(web[k])}")
    lines += ["", "[battery]"]
    for k in ("source", "command"):
        if k in battery:
            lines.append(f"{k} = {_fmt(battery[k])}")
    if fleet:
        lines += ["", "[fleet]"]
        for k in ("key",):
            if k in fleet:
                lines.append(f"{k} = {_fmt(fleet[k])}")
    return "\n".join(lines) + "\n"


def write(home: str, text: str) -> str:
    os.makedirs(home, exist_ok=True)
    path = config_path(home)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def config_path(home: str) -> str:
    return os.path.join(home, CONFIG_NAME)


def _parse_scalar(raw: str) -> Any:
    raw = raw.strip()
    # strip trailing inline comment (not inside quotes)
    if raw and raw[0] not in "\"'":
        hashpos = raw.find("#")
        if hashpos != -1:
            raw = raw[:hashpos].strip()
    if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
        return raw[1:-1]
    low = raw.lower()
    if low in ("true", "false"):
        return low == "true"
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def _parse_toml_min(text: str) -> Dict[str, Dict[str, Any]]:
    data: Dict[str, Dict[str, Any]] = {}
    section = None
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("[") and s.endswith("]"):
            section = s[1:-1].strip()
            data.setdefault(section, {})
            continue
        if "=" in s and section is not None:
            k, v = s.split("=", 1)
            data[section][k.strip()] = _parse_scalar(v)
    return data


def load(home: str) -> Dict[str, Dict[str, Any]]:
    path = config_path(home)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
        try:
            import tomllib  # Python 3.11+
            return tomllib.loads(raw.decode("utf-8"))
        except Exception:
            return _parse_toml_min(raw.decode("utf-8"))
    except Exception:
        return {}


def write_default(home: str, force: bool = False) -> str:
    os.makedirs(home, exist_ok=True)
    path = config_path(home)
    if os.path.exists(path) and not force:
        return path
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(DEFAULT_TOML)
    return path


def update(home: str, eink: Dict[str, Any] = None, buttons: Dict[str, Any] = None,
           web: Dict[str, Any] = None, battery: Dict[str, Any] = None,
           fleet: Dict[str, Any] = None) -> str:
    """Merge changes into the existing config and rewrite it (preserves the rest)."""
    cur = load(home)
    e = dict(cur.get("eink", {}))
    if eink:
        e.update(eink)
    b = dict(cur.get("buttons", {})) or {"feed": 5, "meditate": 6, "pet": 16,
                                         "cast": 24, "deed": 26}
    if buttons:
        b.update(buttons)
    w = dict(cur.get("web", {})) or {"host": "127.0.0.1", "port": 8777}
    if web:
        w.update(web)
    bat = dict(cur.get("battery", {}))
    if battery:
        bat.update(battery)
    flt = dict(cur.get("fleet", {}))
    if fleet:
        flt.update(fleet)
    return write(home, build_toml(e, b, w, bat, flt or None))


def pins_from_config(cfg: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for name, val in (cfg.get("buttons") or {}).items():
        try:
            out[name] = int(val)
        except (TypeError, ValueError):
            pass
    return out
