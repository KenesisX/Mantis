"""Optional BLE proximity sensor for MANTIS discovery.

Detects other MANTIS units over Bluetooth Low Energy by their advertised local
name: ``MANTIS|<id>|<name>|<level>|<power>``. Pure RX scanning — it only listens
for advertisements others broadcast about themselves, exactly like any BLE scan.

This module imports cleanly with or without ``bleak``; if the library or a
Bluetooth adapter is missing, :func:`start_ble` returns ``False`` and Wi-Fi
discovery carries on unaffected. To also *advertise* over BLE (so button-less
units find each other without Wi-Fi), see INSTALL-PI.md — it uses BlueZ and is
set up by the installer when a Bluetooth adapter is present.
"""

from __future__ import annotations

import threading
from typing import Any, Dict

NAME_PREFIX = "MANTIS|"


def _parse(name: str) -> Dict[str, Any] | None:
    if not name or not name.startswith(NAME_PREFIX):
        return None
    try:
        _, pid, nm, lvl, pw = (name.split("|") + ["", "", "0", "1"])[:5]
        return {"id": pid, "name": nm or "ble-mantis",
                "level": int(lvl or 0), "power": int(pw or 1)}
    except Exception:
        return None


def start_ble(engine, disco) -> bool:
    """Start a background BLE scanner feeding peers into ``disco``. Best-effort."""
    try:
        import bleak  # noqa: F401
        from bleak import BleakScanner
    except Exception:
        return False

    import asyncio

    def _detection(device, adv):
        info = _parse(getattr(adv, "local_name", None) or getattr(device, "name", ""))
        if info:
            info["mac"] = getattr(device, "address", None)
            disco.add_external_peer(info, via="ble")

    async def _run():
        try:
            scanner = BleakScanner(detection_callback=_detection)
            await scanner.start()
            while True:
                await asyncio.sleep(3600)
        except Exception:
            return

    def _thread():
        try:
            asyncio.run(_run())
        except Exception:
            pass

    threading.Thread(target=_thread, daemon=True).start()
    return True
