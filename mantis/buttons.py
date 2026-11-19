"""Physical GPIO buttons for the Raspberry Pi handheld.

Maps real buttons to pet actions (feed / meditate / pet / cast / deed). Works on
any Pi via RPi.GPIO; if that library is missing (e.g. on a laptop), it degrades
to a no-op so the rest of the program runs unchanged.

Default pin map (BCM numbering) matches the common 4-button e-ink setups
(e.g. Inky Impression / Waveshare button add-ons). Override with --pins or the
MANTIS_PINS env var, e.g.  MANTIS_PINS="feed=5,meditate=6,pet=16,cast=24,deed=26".
"""

from __future__ import annotations

import os
import threading
from typing import Callable, Dict, Optional

DEFAULT_PINS: Dict[str, int] = {
    "feed": 5, "meditate": 6, "pet": 16, "cast": 24, "deed": 26,
}


def parse_pins(spec: Optional[str]) -> Dict[str, int]:
    pins = dict(DEFAULT_PINS)
    spec = spec or os.environ.get("MANTIS_PINS") or os.environ.get("PSYCHOMANTIS_PINS")
    if spec:
        for part in spec.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                try:
                    pins[k.strip()] = int(v)
                except ValueError:
                    pass
    return pins


class ButtonPad:
    """Wires GPIO pins to callbacks, with two-button combo detection.

    A single press fires its action after a short ``combo_ms`` window; if a
    second mapped button is pressed inside that window and the pair has a combo
    bound, the pending singles are cancelled and the combo fires instead. So you
    can hold two buttons together for a shortcut without triggering the singles.

    ``combos`` maps a frozenset of two action-names to a callable, e.g.
    ``{frozenset({"feed", "pet"}): soothe}``.  Safe no-op without GPIO.
    """

    def __init__(self, actions: Dict[str, Callable[[], None]],
                 combos: Optional[Dict[frozenset, Callable[[], None]]] = None,
                 pins: Optional[Dict[str, int]] = None,
                 bounce_ms: int = 250, combo_ms: int = 350,
                 hold_combos: Optional[Dict[frozenset, Callable[[], None]]] = None,
                 hold_seconds: float = 3.0, on_hold_start=None, on_hold_cancel=None):
        self.available = False
        self._actions = actions
        self._combos = combos or {}
        self._hold_combos = hold_combos or {}
        self._hold_s = hold_seconds
        self._on_hold_start = on_hold_start
        self._on_hold_cancel = on_hold_cancel
        self._pins = pins or parse_pins(None)
        self._combo_s = combo_ms / 1000.0
        self._lock = threading.RLock()
        self._pending: Dict[str, float] = {}
        self._timers: Dict[str, threading.Timer] = {}
        self._pressed_override = None     # for testing without GPIO
        self.GPIO = None
        try:
            import RPi.GPIO as GPIO  # type: ignore
            self.GPIO = GPIO
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            for name in actions:
                pin = self._pins.get(name)
                if pin is None:
                    continue
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(
                    pin, GPIO.FALLING,
                    callback=self._make_handler(name), bouncetime=bounce_ms)
            self.available = True
        except Exception:
            self.available = False

    def _make_handler(self, name: str):
        def handler(_pin=None):
            self.press(name)
        return handler

    def press(self, name: str) -> None:
        """Register a press (also callable directly for testing)."""
        import time
        now = time.time()
        with self._lock:
            # does this complete a HOLD-combo with a recent pending press?
            for other, t in list(self._pending.items()):
                pair = frozenset((name, other))
                if pair in self._hold_combos and now - t <= self._combo_s:
                    self._cancel(other)
                    self._pending.pop(other, None)
                    self._arm_hold(pair, self._hold_combos[pair])
                    return
            # does this complete a regular combo with a recent pending press?
            for other, t in list(self._pending.items()):
                combo = self._combos.get(frozenset((name, other)))
                if combo is not None and now - t <= self._combo_s:
                    self._cancel(other)
                    self._pending.pop(other, None)
                    self._run(combo)
                    return
            # otherwise hold the single briefly in case a combo partner arrives
            self._pending[name] = now
            if self._combos or self._hold_combos:
                timer = threading.Timer(self._combo_s, self._fire_single, args=(name,))
                self._timers[name] = timer
                timer.daemon = True
                timer.start()
            else:
                self._fire_single(name)

    def _fire_single(self, name: str) -> None:
        with self._lock:
            if name not in self._pending:
                return
            self._pending.pop(name, None)
            self._timers.pop(name, None)
            cb = self._actions.get(name)
        if cb:
            self._run(cb)

    def _cancel(self, name: str) -> None:
        t = self._timers.pop(name, None)
        if t is not None:
            t.cancel()

    # -- hold combos (e.g. hold two buttons 3s to power off) ------------ #
    def _pin_pressed(self, name: str) -> bool:
        if self._pressed_override is not None:
            return bool(self._pressed_override(name))
        pin = self._pins.get(name)
        if pin is None or self.GPIO is None:
            return False
        try:
            return self.GPIO.input(pin) == 0        # pull-up: pressed == LOW
        except Exception:
            return False

    def _arm_hold(self, pair: frozenset, cb: Callable[[], None]) -> None:
        # a physical hold can only be verified with GPIO (or an injected override)
        if self._pressed_override is None and self.GPIO is None:
            return
        if self._on_hold_start:
            self._run(lambda: self._on_hold_start(pair))
        t = threading.Thread(target=self._hold_watch, args=(pair, cb), daemon=True)
        t.start()

    def _hold_watch(self, pair: frozenset, cb: Callable[[], None]) -> None:
        import time
        names = list(pair)
        deadline = time.time() + self._hold_s
        while time.time() < deadline:
            if not all(self._pin_pressed(n) for n in names):
                if self._on_hold_cancel:
                    self._run(lambda: self._on_hold_cancel(pair))
                return
            time.sleep(0.1)
        self._run(cb)

    @staticmethod
    def _run(cb: Callable[[], None]) -> None:
        try:
            cb()
        except Exception:
            pass

    def describe(self) -> str:
        singles = ", ".join(f"{n}=GPIO{self._pins.get(n)}" for n in self._actions)
        extra = ""
        if self._combos:
            extra += "  | combos: " + "; ".join("+".join(sorted(k)) for k in self._combos)
        if self._hold_combos:
            extra += "  | hold: " + "; ".join(
                "+".join(sorted(k)) + f"({self._hold_s:g}s)" for k in self._hold_combos)
        return singles + extra

    def cleanup(self) -> None:
        for t in list(self._timers.values()):
            try:
                t.cancel()
            except Exception:
                pass
        if self.GPIO is not None:
            try:
                self.GPIO.cleanup()
            except Exception:
                pass
