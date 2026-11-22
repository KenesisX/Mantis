"""The Spellbook — MANTIS' tools, reframed as psychic abilities.

Every spell maps to a REAL but deliberately safe/benign operation:

* passive Wi-Fi *listing* (the same read-only info your OS already shows),
* mapping *your own* local subnet (host discovery on your LAN),
* auditing *your own* machine's listening ports,
* ordinary network diagnostics (ping / traceroute / DNS) that any user may run,
* and purely cosmetic "psychic theatre" effects.

There is intentionally NO deauthentication, packet injection, monitor-mode
capture, handshake harvesting or password cracking anywhere in this file.
If a platform tool is missing, the spell falls back to a thematic simulation
so the pet always "works everywhere".
"""

from __future__ import annotations

import ipaddress
import platform
import random
import re
import shutil
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from . import personality as P
from .engine import Engine


# --------------------------------------------------------------------------- #
# Spell definition
# --------------------------------------------------------------------------- #
@dataclass
class Spell:
    id: str
    name: str
    glyph: str
    min_level: int
    psyche_cost: int
    xp: int
    school: str
    desc: str
    run: Callable[[Engine], Dict[str, Any]]


SPELLS: Dict[str, "Spell"] = {}


def register(**kw: Any):
    def deco(fn: Callable[[Engine], Dict[str, Any]]):
        sp = Spell(run=fn, **kw)
        SPELLS[sp.id] = sp
        return fn
    return deco


class SpellError(Exception):
    pass


# --------------------------------------------------------------------------- #
# Casting
# --------------------------------------------------------------------------- #
def cast(engine: Engine, spell_id: str) -> Dict[str, Any]:
    spell = SPELLS.get(spell_id)
    if spell is None:
        raise SpellError(f"No such spell: {spell_id}")
    pet = engine.pet
    if spell_id not in pet.unlocked_spells and spell.min_level > pet.level:
        raise SpellError(f"{spell.name} requires level {spell.min_level}.")
    if pet.psyche < spell.psyche_cost:
        raise SpellError(f"Not enough PSYCHE ({int(pet.psyche)}/{spell.psyche_cost}).")

    engine.emit("cast", f"Casting {spell.name}...", spell=spell_id)
    engine._hold_mood("casting", 6)
    with engine._lock:
        pet.psyche = max(0.0, pet.psyche - spell.psyche_cost)
        pet.focus = max(0.0, pet.focus - 4)
        pet.spells_cast += 1

    try:
        result = spell.run(engine) or {}
    except Exception as exc:  # never let a spell crash the pet
        result = {"summary": f"The vision failed: {exc}", "items": [], "ok": False}

    engine._award(spell.xp, reason=spell.name)
    try:
        engine.note_affinity(spell_id)      # learn what the keeper gravitates to
    except Exception:
        pass
    try:
        from . import coach as _COACH
        engine.coach_after(_COACH.SPELL_CAT.get(spell_id, "recon"), "cast:" + spell_id)
    except Exception:
        pass
    summary = result.get("summary", f"{spell.name} complete.")
    engine.emit("result", summary, spell=spell_id, ok=result.get("ok", True))
    # teachable moment: surface the real concept behind this spell
    try:
        from . import academy as _ACAD
        les = _ACAD.spell_lesson(spell_id)
        if les and les["id"] not in engine.pet.academy.get("introduced", []):
            engine.introduce_lesson(les["id"])
            engine.emit("learn", f"📖 {les['title']}: {les['body'][:90]}... "
                                 f"(learn: mantis learn {les['id']})")
            result["lesson"] = _ACAD.public_lesson(les)
    except Exception:
        pass
    engine._after_action()
    result.setdefault("spell", spell.name)
    result.setdefault("ok", True)
    return result


# --------------------------------------------------------------------------- #
# Low-level helpers (all benign)
# --------------------------------------------------------------------------- #
def _run(cmd: List[str], timeout: int = 12) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (out.stdout or "") + (out.stderr or "")
    except Exception:
        return ""


def _have(tool: str) -> bool:
    return shutil.which(tool) is not None


def _local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def _ping_once(host: str, timeout_ms: int = 600) -> bool:
    system = platform.system().lower()
    if "windows" in system:
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), host]
    else:
        cmd = ["ping", "-c", "1", "-W", str(max(1, timeout_ms // 1000)), host]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        return r.returncode == 0
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# SPELL 1 — Mind Reading : passive Wi-Fi listing
# --------------------------------------------------------------------------- #
@register(id="mind_reading", name="Mind Reading", glyph="👁", min_level=1,
          psyche_cost=5, xp=12, school="Divination",
          desc="Reach into the ether and hear the minds (Wi-Fi networks) nearby. "
               "Passive listening only — the same networks your phone already sees.")
def _mind_reading(engine: Engine) -> Dict[str, Any]:
    nets = _scan_wifi()
    with engine._lock:
        engine.pet.networks_sensed += len(nets)
        seen = {n["ssid"] for n in engine.pet.known_networks}
        for n in nets:
            if n["ssid"] not in seen:
                engine.pet.known_networks.append(n)
        engine.pet.known_networks = engine.pet.known_networks[-200:]
    engine._check_achievements()
    if nets:
        top = max(nets, key=lambda n: n.get("signal", 0))
        summary = f"I hear {len(nets)} minds. The loudest is '{top['ssid']}'."
    else:
        summary = "Silence... no minds within reach."
    return {"summary": summary, "items": nets, "count": len(nets)}


def _scan_wifi() -> List[Dict[str, Any]]:
    system = platform.system().lower()
    nets: List[Dict[str, Any]] = []
    try:
        if "linux" in system and _have("nmcli"):
            raw = _run(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,CHAN", "dev", "wifi"])
            for line in raw.splitlines():
                parts = line.split(":")
                if not parts or not parts[0]:
                    continue
                nets.append({
                    "ssid": parts[0],
                    "signal": _to_int(parts[1]) if len(parts) > 1 else 0,
                    "security": parts[2] if len(parts) > 2 else "?",
                    "channel": parts[3] if len(parts) > 3 else "?",
                })
        elif "darwin" in system:
            airport = ("/System/Library/PrivateFrameworks/Apple80211.framework/"
                       "Versions/Current/Resources/airport")
            raw = _run([airport, "-s"])
            for line in raw.splitlines()[1:]:
                m = re.match(r"\s*(.+?)\s+([0-9a-f:]{17})\s+(-?\d+)\s+(\S+)", line)
                if m:
                    nets.append({"ssid": m.group(1).strip(),
                                 "bssid": m.group(2),
                                 "signal": _rssi_to_pct(_to_int(m.group(3))),
                                 "security": "?", "channel": m.group(4)})
        elif "windows" in system:
            raw = _run(["netsh", "wlan", "show", "networks", "mode=bssid"])
            cur: Dict[str, Any] = {}
            for line in raw.splitlines():
                line = line.strip()
                if line.lower().startswith("ssid ") and ":" in line:
                    if cur.get("ssid"):
                        nets.append(cur)
                    cur = {"ssid": line.split(":", 1)[1].strip() or "<hidden>",
                           "signal": 0, "security": "?", "channel": "?"}
                elif line.lower().startswith("signal") and ":" in line:
                    cur["signal"] = _to_int(line.split(":", 1)[1])
                elif line.lower().startswith("authentication") and ":" in line:
                    cur["security"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("channel") and ":" in line:
                    cur["channel"] = line.split(":", 1)[1].strip()
            if cur.get("ssid"):
                nets.append(cur)
    except Exception:
        pass
    if not nets:
        nets = _simulate_wifi()
    # de-dup by ssid keeping strongest
    best: Dict[str, Dict[str, Any]] = {}
    for n in nets:
        k = n["ssid"]
        if k not in best or n.get("signal", 0) > best[k].get("signal", 0):
            best[k] = n
    return sorted(best.values(), key=lambda n: n.get("signal", 0), reverse=True)


def _simulate_wifi() -> List[Dict[str, Any]]:
    names = ["Shadow_Moses_Guest", "OuterHeaven", "NOMAD-2.4G", "Codec_140.85",
             "PentaDrive", "FOXDIE_lab", "Metal_Gear_WiFi", "Gray_Fox",
             "theBossNet", "DIAMOND_DOGS", "NASTASHA-5G", "HIND-D"]
    secs = ["WPA2", "WPA3", "WPA2", "OPEN", "WPA2-Enterprise"]
    random.shuffle(names)
    out = []
    for nm in names[: random.randint(4, 9)]:
        out.append({"ssid": nm, "signal": random.randint(22, 95),
                    "security": random.choice(secs),
                    "channel": str(random.choice([1, 6, 11, 36, 44, 149])),
                    "sim": True})
    return out


# --------------------------------------------------------------------------- #
# SPELL 2 — Clairvoyance : map YOUR OWN local subnet
# --------------------------------------------------------------------------- #
@register(id="clairvoyance", name="Clairvoyance", glyph="🔮", min_level=2,
          psyche_cost=12, xp=20, school="Divination",
          desc="See every device dwelling on YOUR OWN local network. Benign host "
               "discovery (ping sweep) of your /24 — the same as 'who's on my Wi-Fi'.")
def _clairvoyance(engine: Engine) -> Dict[str, Any]:
    ip = _local_ip()
    if ip.startswith("127."):
        hosts = _simulate_hosts()
    else:
        try:
            net = ipaddress.ip_network(ip + "/24", strict=False)
            targets = [str(h) for h in net.hosts()]
        except Exception:
            targets = []
        hosts = []
        with ThreadPoolExecutor(max_workers=64) as ex:
            results = list(ex.map(lambda h: (h, _ping_once(h, 500)), targets))
        for h, alive in results:
            if alive:
                name = _reverse_dns(h)
                hosts.append({"ip": h, "name": name, "alive": True})
        if not hosts:
            hosts = _simulate_hosts()
    with engine._lock:
        engine.pet.devices_read += len(hosts)
        known = {d["ip"] for d in engine.pet.known_devices}
        for h in hosts:
            if h["ip"] not in known:
                engine.pet.known_devices.append(h)
        engine.pet.known_devices = engine.pet.known_devices[-200:]
    engine._check_achievements()
    summary = f"I see {len(hosts)} souls sharing your network."
    return {"summary": summary, "items": hosts, "count": len(hosts), "subnet": ip + "/24"}


def _reverse_dns(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return "unknown"


def _simulate_hosts() -> List[Dict[str, Any]]:
    base = "192.168.1."
    names = ["router.home", "nastasha-laptop", "codec-phone", "retro-console",
             "printer", "nas-shadowmoses", "iot-lamp", "unknown"]
    out = []
    for i in random.sample(range(2, 60), random.randint(3, 7)):
        out.append({"ip": base + str(i), "name": random.choice(names),
                    "alive": True, "sim": True})
    return out


# --------------------------------------------------------------------------- #
# SPELL 3 — The Veil : audit YOUR OWN machine's open ports (defensive)
# --------------------------------------------------------------------------- #
@register(id="the_veil", name="The Veil", glyph="🛡", min_level=3,
          psyche_cost=14, xp=24, school="Abjuration",
          desc="Look inward at your OWN machine and reveal which doors (listening "
               "ports) stand open, so you may ward them. Scans 127.0.0.1 only.")
def _the_veil(engine: Engine) -> Dict[str, Any]:
    common = {
        22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP",
        110: "POP3", 139: "NetBIOS", 143: "IMAP", 443: "HTTPS", 445: "SMB",
        3306: "MySQL", 3389: "RDP", 5432: "Postgres", 5900: "VNC",
        6379: "Redis", 8080: "HTTP-alt", 8443: "HTTPS-alt", 27017: "MongoDB",
    }
    open_ports = []
    for port, svc in common.items():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.25)
        try:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                risky = port in (23, 3389, 5900, 445, 6379, 27017, 3306, 5432)
                open_ports.append({"port": port, "service": svc, "risky": risky})
        except Exception:
            pass
        finally:
            s.close()
    if open_ports:
        risky = [p for p in open_ports if p["risky"]]
        if risky:
            summary = (f"{len(open_ports)} doors stand open on your own fortress — "
                       f"{len(risky)} are dangerously exposed. Ward them.")
        else:
            summary = f"{len(open_ports)} doors open on your machine, none alarming."
    else:
        summary = "Your fortress is sealed. No open doors found. Impressive."
    return {"summary": summary, "items": open_ports, "count": len(open_ports)}


# --------------------------------------------------------------------------- #
# SPELL 4 — Telepathy : is a known host 'home'? (ping your own devices)
# --------------------------------------------------------------------------- #
@register(id="telepathy", name="Telepathy", glyph="📡", min_level=4,
          psyche_cost=10, xp=18, school="Divination",
          desc="Reach out to the devices you already know and sense which are "
               "present. Benign reachability check (ping) of remembered hosts.")
def _telepathy(engine: Engine) -> Dict[str, Any]:
    known = list(engine.pet.known_devices)[-20:]
    if not known:
        return {"summary": "I know no minds yet. Cast Clairvoyance first.",
                "items": [], "count": 0, "ok": True}
    present = []
    with ThreadPoolExecutor(max_workers=32) as ex:
        res = list(ex.map(lambda d: (d, _ping_once(d["ip"], 500)), known))
    for d, alive in res:
        present.append({**d, "present": bool(alive)})
    here = sum(1 for p in present if p["present"])
    summary = f"{here} of {len(present)} familiar minds are present right now."
    return {"summary": summary, "items": present, "count": here}


# --------------------------------------------------------------------------- #
# SPELL 5 — Astral Projection : traceroute a host (ordinary diagnostic)
# --------------------------------------------------------------------------- #
@register(id="astral_projection", name="Astral Projection", glyph="🌌", min_level=5,
          psyche_cost=16, xp=26, school="Conjuration",
          desc="Send your spirit across the astral plane to a distant host and map "
               "the path your thoughts travel (traceroute).")
def _astral(engine: Engine, host: str = "1.1.1.1") -> Dict[str, Any]:
    system = platform.system().lower()
    tool = "tracert" if "windows" in system else "traceroute"
    hops: List[Dict[str, Any]] = []
    if _have(tool):
        flag = [] if "windows" in system else ["-m", "12", "-w", "1"]
        raw = _run([tool, *flag, host], timeout=20)
        for line in raw.splitlines():
            m = re.search(r"\(?(\d{1,3}(?:\.\d{1,3}){3})\)?", line)
            if m:
                hops.append({"hop": len(hops) + 1, "ip": m.group(1)})
    if not hops:
        hops = [{"hop": i + 1, "ip": f"10.{random.randint(0,255)}."
                 f"{random.randint(0,255)}.{random.randint(1,254)}", "sim": True}
                for i in range(random.randint(5, 9))]
    summary = f"My spirit crossed {len(hops)} realms to reach {host}."
    return {"summary": summary, "items": hops, "count": len(hops), "target": host}


# --------------------------------------------------------------------------- #
# SPELL 6 — Hydro-Quartz Gaze : resolve a name (DNS lookup)
# --------------------------------------------------------------------------- #
@register(id="hydroquartz", name="Hydro-Quartz Gaze", glyph="💠", min_level=6,
          psyche_cost=8, xp=16, school="Divination",
          desc="Gaze through the crystal and bind a name to its true address "
               "(DNS resolution).")
def _hydroquartz(engine: Engine, name: str = "example.com") -> Dict[str, Any]:
    try:
        infos = socket.getaddrinfo(name, None)
        addrs = sorted({i[4][0] for i in infos})
        summary = f"'{name}' reveals its true form: {', '.join(addrs[:4])}."
        items = [{"address": a} for a in addrs]
    except Exception:
        summary = f"The crystal clouds over. '{name}' hides from me."
        items = []
    return {"summary": summary, "items": items, "count": len(items), "target": name}


# --------------------------------------------------------------------------- #
# SPELL 7 — Psychokinesis : cosmetic "move the controller" theatre
# --------------------------------------------------------------------------- #
@register(id="psychokinesis", name="Psychokinesis", glyph="✨", min_level=7,
          psyche_cost=20, xp=22, school="Evocation",
          desc="Bend the physical world. (A dramatic flourish — makes the display "
               "tremble. Performs no network action whatsoever.)")
def _psychokinesis(engine: Engine) -> Dict[str, Any]:
    tricks = [
        "I move your cursor with my mind. Did you feel that?",
        "Your controller trembles in my grip.",
        "The screen bends to my will. Observe.",
        "I lift the machine with a thought alone.",
    ]
    with engine._lock:
        engine.pet.psyche = min(100.0, engine.pet.psyche + 4)  # showmanship feeds him
    return {"summary": P.pick(tricks), "items": [], "effect": "shake", "count": 0}


# --------------------------------------------------------------------------- #
# SPELL 8 — Soul Scream : ultimate (cosmetic, huge XP, big cost)
# --------------------------------------------------------------------------- #
@register(id="soul_scream", name="Soul Scream", glyph="🔥", min_level=10,
          psyche_cost=60, xp=120, school="Forbidden",
          desc="Unleash the full anguish of a thousand minds. A devastating "
               "psychic cry. (Purely theatrical — great power, great XP.)")
def _soul_scream(engine: Engine) -> Dict[str, Any]:
    lines = [
        "AAAAAHHHH!!! Feel the sorrow of everyone I have ever touched!",
        "The scream of a thousand abandoned souls pours out of me!",
        "I let it ALL out — every thought, every pain, at once!",
    ]
    with engine._lock:
        engine.pet.sanity = max(0.0, engine.pet.sanity - 12)  # it costs him dearly
    return {"summary": P.pick(lines), "items": [], "effect": "scream", "count": 0}


# --------------------------------------------------------------------------- #
# Autonomous passive tick (pwnagotchi-style "lives on its own")
# --------------------------------------------------------------------------- #
def autonomous_sense(engine: Engine) -> None:
    """Occasionally sense the ether by itself, if it has the psyche to spare."""
    pet = engine.pet
    if pet.mood == "sleeping" or pet.psyche < 10:
        return
    if random.random() < 0.5:
        try:
            nets = _scan_wifi()
            new = [n for n in nets
                   if n["ssid"] not in {k["ssid"] for k in pet.known_networks}]
            with engine._lock:
                pet.networks_sensed += len(nets)
                for n in new:
                    pet.known_networks.append(n)
                pet.known_networks = pet.known_networks[-200:]
                pet.psyche = max(0.0, pet.psyche - 3)
            engine._award(2 + len(new))
            if new:
                engine.emit("idle_scan",
                            f"{P.pick(P.PHRASES['idle_scan'])} (+{len(new)} new)")
            engine._check_achievements()
        except Exception:
            pass


def _to_int(s: str) -> int:
    m = re.search(r"-?\d+", s or "")
    return int(m.group()) if m else 0


def _rssi_to_pct(rssi: int) -> int:
    # map dBm (~ -100..-40) to 0..100
    return max(0, min(100, 2 * (rssi + 100)))


def spell_catalog(unlocked: List[str], level: int) -> List[Dict[str, Any]]:
    out = []
    for sid, sp in SPELLS.items():
        out.append({
            "id": sid, "name": sp.name, "glyph": sp.glyph,
            "min_level": sp.min_level, "psyche_cost": sp.psyche_cost,
            "xp": sp.xp, "school": sp.school, "desc": sp.desc,
            "unlocked": sid in unlocked or sp.min_level <= level,
        })
    return sorted(out, key=lambda s: s["min_level"])


# receive-only RF / SDR spells (Xenu flavour) — registers additional spells
try:
    from . import rf_spells as _rf_spells  # noqa: F401
except Exception:
    pass

# defensive, read-only blue-team spells — registers additional spells
try:
    from . import defense_spells as _defense_spells  # noqa: F401
except Exception:
    pass
