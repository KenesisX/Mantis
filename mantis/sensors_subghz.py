"""Optional Sub-GHz proximity sensor for MANTIS discovery (RECEIVE-ONLY).

If you have an SDR (RTL-SDR, etc.) and ``rtl_433`` installed, MANTIS can *listen*
on the ISM bands for other units announcing themselves and add them as peers.
This is strictly receive-only — it never transmits. Transmitting on Sub-GHz is
regulated and is deliberately not implemented anywhere in MANTIS.

Imports cleanly without any SDR tooling; :func:`start_subghz` returns ``False``
when ``rtl_433`` isn't on PATH, and other discovery radios carry on. A companion
beacon (how a unit announces itself over Sub-GHz) is left to hardware-specific
setup; see INSTALL-PI.md.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import threading
from typing import Any, Dict, Optional


def _parse(line: str) -> Optional[Dict[str, Any]]:
    """Look for a MANTIS self-announcement embedded in an rtl_433 JSON event."""
    try:
        obj = json.loads(line)
    except Exception:
        return None
    # a MANTIS sub-ghz beacon tags its payload with model 'MANTIS'
    if str(obj.get("model", "")).upper() != "MANTIS":
        return None
    return {"id": str(obj.get("id", "")), "name": obj.get("name", "subghz-mantis"),
            "level": int(obj.get("level", 0) or 0), "power": int(obj.get("power", 1) or 1)}


def start_subghz(engine, disco) -> bool:
    """Start an rtl_433 listener feeding peers into ``disco``. Receive-only."""
    if not shutil.which("rtl_433"):
        return False

    def _thread():
        try:
            proc = subprocess.Popen(
                ["rtl_433", "-F", "json", "-M", "level"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            for line in proc.stdout:               # type: ignore[union-attr]
                info = _parse(line)
                if info and info["id"]:
                    disco.add_external_peer(info, via="subghz")
        except Exception:
            return

    threading.Thread(target=_thread, daemon=True).start()
    return True
