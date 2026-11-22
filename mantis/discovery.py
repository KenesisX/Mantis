"""LAN proximity discovery — MANTIS senses other MANTIS units nearby.

Each MANTIS periodically sends a tiny UDP broadcast "beacon" on the local
network and listens for others. When it hears another MANTIS it adds it to a
peer list; the pet can then challenge it to a duel (see ``duel.py``).

Scope / safety: this only BROADCASTS a small self-describing packet (name, id,
level, power, web port) on the LAN and listens for the same — exactly like mDNS
service announcement. It performs no scanning, no connection to anyone else's
device, and reads nothing a peer didn't choose to broadcast about itself. It is
opt-in (config ``[discovery] enabled``) and confined to the local subnet via
UDP broadcast; it never leaves your network.
"""

from __future__ import annotations

import json
import socket
import threading
import time
from typing import Any, Dict, List, Optional

PROTO = "mantis-v1"
PORT = 8778                    # UDP beacon port
BEACON_EVERY = 8.0            # seconds between our beacons
PEER_TTL = 40.0              # drop a peer we haven't heard from in this long
MAX_PKT = 2048


class Discovery:
    """A background LAN beacon + listener maintaining a peer table."""

    def __init__(self, self_fn, port: int = PORT):
        """``self_fn()`` returns our current beacon dict (id, name, level, power...)."""
        self._self_fn = self_fn
        self.port = port
        self._peers: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._tx: Optional[socket.socket] = None
        self._on_new = None            # optional callback(peer) for a freshly-seen peer
        self._my_id = None

    def on_new_peer(self, fn) -> None:
        self._on_new = fn

    # -- lifecycle ----------------------------------------------------- #
    def start(self) -> "Discovery":
        threading.Thread(target=self._recv_loop, daemon=True).start()
        threading.Thread(target=self._beacon_loop, daemon=True).start()
        return self

    def stop(self) -> None:
        self._stop.set()

    # -- peers --------------------------------------------------------- #
    def peers(self, include_stale: bool = False) -> List[Dict[str, Any]]:
        now = time.time()
        with self._lock:
            out = []
            for p in self._peers.values():
                ago = now - p.get("_seen", 0)
                if not include_stale and ago > PEER_TTL:
                    continue
                q = dict(p)
                q.pop("_seen", None)
                q["ago"] = int(ago)
                q["online"] = ago < PEER_TTL
                out.append(q)
            return sorted(out, key=lambda d: (not d["online"], -int(d.get("power", 0))))

    def get(self, peer_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            p = self._peers.get(peer_id)
            return dict(p) if p else None

    # -- internals ----------------------------------------------------- #
    def _beacon(self) -> bytes:
        try:
            info = dict(self._self_fn() or {})
        except Exception:
            info = {}
        info["proto"] = PROTO
        self._my_id = info.get("id")
        return json.dumps(info).encode("utf-8")[:MAX_PKT]

    def _beacon_loop(self) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception:
            pass
        self._tx = s
        while not self._stop.is_set():
            try:
                s.sendto(self._beacon(), ("255.255.255.255", self.port))
            except Exception:
                pass
            self._stop.wait(BEACON_EVERY)

    def _recv_loop(self) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except (AttributeError, OSError):
                pass
            s.bind(("", self.port))
        except Exception:
            return
        s.settimeout(1.0)
        while not self._stop.is_set():
            try:
                data, addr = s.recvfrom(MAX_PKT)
            except socket.timeout:
                continue
            except Exception:
                continue
            try:
                info = json.loads(data.decode("utf-8", "ignore"))
            except Exception:
                continue
            if not isinstance(info, dict) or info.get("proto") != PROTO:
                continue
            pid = str(info.get("id") or "")
            if not pid or pid == self._my_id:        # ignore ourselves
                continue
            info["ip"] = info.get("ip") or addr[0]
            info.setdefault("via", "wifi")
            self.add_external_peer(info, info["via"])

    def add_external_peer(self, info: Dict[str, Any], via: str = "wifi") -> None:
        """Register a peer seen over ANY radio (Wi-Fi recv loop, or a BLE / Sub-GHz
        sensor backend). Safe to call from other threads."""
        pid = str(info.get("id") or "")
        if not pid or pid == self._my_id:
            return
        info = dict(info)
        info["via"] = via
        info["_seen"] = time.time()
        with self._lock:
            fresh = pid not in self._peers
            self._peers[pid] = info
        if fresh and self._on_new:
            try:
                self._on_new(dict(info))
            except Exception:
                pass


def own_mac() -> str:
    import uuid
    n = uuid.getnode()
    return ":".join(f"{(n >> (8 * i)) & 0xFF:02X}" for i in reversed(range(6)))


def beacon_from_engine(engine) -> Dict[str, Any]:
    """Build our beacon payload from the live engine snapshot (self-disclosed)."""
    from . import fleet, duel
    snap = engine.snapshot()
    stg = snap.get("stage") or {}
    return {
        "id": fleet._device_id(engine.home),
        "name": __import__("socket").gethostname(),
        "level": snap.get("level"),
        "rank": snap.get("rank"),
        "power": duel.power(snap),
        "stage": stg.get("label"),
        "stage_key": stg.get("key"),
        "mood": snap.get("mood"),
        "verified": bool(snap.get("verified", True)),
        "ip": fleet._local_ip(),
        "mac": own_mac(),
        "web": getattr(engine, "_web_port", 8777),
        "via": "wifi",
    }


def start_extra_sensors(engine, disco: "Discovery") -> List[str]:
    """Best-effort BLE / Sub-GHz discovery backends. Each announces a MANTIS over
    another radio and feeds peers into ``disco.add_external_peer(info, via)``.

    These are OPTIONAL and degrade silently: on hardware without the radio or the
    optional library they simply don't start, and Wi-Fi/LAN discovery carries on.
    Returns the list of sensors that started.
    """
    started: List[str] = []
    # --- BLE (needs 'bleak' + a Bluetooth adapter) --------------------------
    try:
        import importlib
        if importlib.util.find_spec("bleak") is not None:
            from .sensors_ble import start_ble      # thin, optional module
            if start_ble(engine, disco):
                started.append("ble")
    except Exception:
        pass
    # --- Sub-GHz (needs an SDR + rtl_433; receive-only) ---------------------
    try:
        from .sensors_subghz import start_subghz
        if start_subghz(engine, disco):
            started.append("subghz")
    except Exception:
        pass
    return started
