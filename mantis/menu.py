"""On-device settings menu model (no GPIO / no rendering here).

Drives an editable list of settings with five actions — up, down (move the
selection), inc, dec (change the selected value) and a save. Values map back to
config.toml sections. The e-ink renderer draws it; the button loop calls its
methods. Kept UI-free so it is easy to test.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class Field:
    def __init__(self, key: str, label: str, section: str, kind: str,
                 value: Any, choices: Optional[list] = None,
                 lo: Optional[int] = None, hi: Optional[int] = None, step: int = 1):
        self.key = key
        self.label = label
        self.section = section          # "eink" | "battery"
        self.kind = kind                # "bool" | "enum" | "int"
        self.value = value
        self.choices = choices or []
        self.lo = lo
        self.hi = hi
        self.step = step

    def inc(self, d: int = 1) -> None:
        if self.kind == "bool":
            self.value = not self.value
        elif self.kind == "enum":
            i = (self.choices.index(self.value) if self.value in self.choices else 0)
            self.value = self.choices[(i + d) % len(self.choices)]
        elif self.kind == "int":
            self.value = int(self.value) + self.step * d
            if self.hi is not None:
                self.value = min(self.hi, self.value)
            if self.lo is not None:
                self.value = max(self.lo, self.value)

    def dec(self) -> None:
        self.inc(-1)

    def display(self) -> str:
        if self.kind == "bool":
            return "ON" if self.value else "off"
        return str(self.value)


def _g(values: Dict[str, Any], key: str, default: Any) -> Any:
    return values.get(key, default)


class SettingsMenu:
    """Editable settings. ``values`` is a flat dict of current settings."""

    def __init__(self, values: Dict[str, Any]):
        v = values or {}
        self.fields: List[Field] = [
            Field("driver", "Panel", "eink", "enum", _g(v, "driver", "auto"),
                  choices=["auto", "waveshare", "inky"]),
            Field("rotate", "Rotate", "eink", "enum", _g(v, "rotate", 0),
                  choices=[0, 90, 180, 270]),
            Field("interval", "Refresh s", "eink", "int", _g(v, "interval", 30),
                  lo=5, hi=120, step=5),
            Field("splash", "Splash", "eink", "bool", _g(v, "splash", True)),
            Field("animate", "Animate", "eink", "bool", _g(v, "animate", True)),
            Field("slideshow", "Slideshow", "eink", "bool", _g(v, "slideshow", True)),
            Field("slideshow_interval", "Slide s", "eink", "int",
                  _g(v, "slideshow_interval", 25), lo=5, hi=120, step=5),
            Field("poweroff_combo", "PowerOff", "eink", "bool",
                  _g(v, "poweroff_combo", True)),
            Field("low_battery", "Low bat%", "eink", "int",
                  _g(v, "low_battery", 20), lo=5, hi=50, step=5),
            Field("sleep_below", "Sleep%", "eink", "int",
                  _g(v, "sleep_below", 6), lo=0, hi=30, step=1),
            Field("battery", "Battery", "battery", "enum", _g(v, "battery", "auto"),
                  choices=["auto", "none", "pisugar", "file", "command"]),
        ]
        self.sel = 0
        self.saved = False

    # -- navigation / edit ------------------------------------------- #
    def up(self) -> None:
        self.sel = (self.sel - 1) % len(self.fields)

    def down(self) -> None:
        self.sel = (self.sel + 1) % len(self.fields)

    def inc(self) -> None:
        self.fields[self.sel].inc()

    def dec(self) -> None:
        self.fields[self.sel].dec()

    # -- output ------------------------------------------------------ #
    def signature(self):
        return (self.sel, tuple(f.display() for f in self.fields))

    def rows(self):
        return [(f.label, f.display(), i == self.sel) for i, f in enumerate(self.fields)]

    def to_updates(self):
        eink = {f.key: f.value for f in self.fields if f.section == "eink"}
        battery = {f.key: f.value for f in self.fields if f.section == "battery"}
        # 'battery' field -> [battery].source
        if "battery" in battery:
            battery = {"source": battery["battery"]}
        return eink, battery
