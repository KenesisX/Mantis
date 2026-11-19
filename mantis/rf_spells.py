"""Receive-only RF spells — the Xenu / RTL-SDR flavour, kept strictly passive.

These add "radio listening" abilities to the spellbook for anyone with an
RTL-SDR dongle (e.g. the RTL-SDR Blog V4). They are RECEIVE-ONLY: they decode
public ISM-band and aircraft broadcasts, or read local log files, the same way
a scanner radio or a weather-station receiver does. There is **no transmit, no
replay, no jamming, no injection** anywhere here — only listening.

If no SDR / tools are present, every spell falls back to a thematic simulation
so the pet still works on any machine.

All of these hook into the existing spellbook via `spells.register`.
"""

from __future__ import annotations

import os
import random
import re
import shutil
import subprocess
from typing import Any, Dict, List

from .spells import register


def _have(tool: str) -> bool:
    return shutil.which(tool) is not None


def _run(cmd: List[str], timeout: int = 12) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (out.stdout or "") + (out.stderr or "")
    except Exception:
        return ""


# --------------------------------------------------------------------------- #
# V4 Ether Attunement — probe the SDR, read the noise floor (RX only)
# --------------------------------------------------------------------------- #
def detect_sdrs() -> List[Dict[str, Any]]:
    """Enumerate attached SDR receivers (RX only). Many device families supported."""
    found: List[Dict[str, Any]] = []
    # RTL-SDR family (incl. RTL-SDR Blog V4 R828D)
    if _have("rtl_test"):
        raw = _run(["rtl_test", "-t"], timeout=5)
        if "Found" in raw and "No supported" not in raw:
            tuner = re.search(r"Tuner:\s*(\S+)", raw)
            found.append({"device": "RTL-SDR", "tuner": tuner.group(1) if tuner else "R820T/R828D"})
    # HackRF One
    if _have("hackrf_info"):
        raw = _run(["hackrf_info"], timeout=5)
        if "Serial" in raw or "Found HackRF" in raw:
            found.append({"device": "HackRF One", "note": "RX used; TX not driven by MANTIS"})
    # USRP / Ettus
    if _have("uhd_find_devices"):
        raw = _run(["uhd_find_devices"], timeout=6)
        if "Device Address" in raw or "type:" in raw:
            found.append({"device": "USRP (Ettus)", "note": "UHD device present"})
    # Airspy
    if _have("airspy_info"):
        raw = _run(["airspy_info"], timeout=5)
        if "Serial" in raw or "Found Airspy" in raw:
            found.append({"device": "Airspy"})
    # SoapySDR (covers LimeSDR, PlutoSDR, SDRplay, etc.)
    if _have("SoapySDRUtil"):
        raw = _run(["SoapySDRUtil", "--find"], timeout=6)
        for m in re.finditer(r"driver\s*=\s*(\S+)", raw):
            found.append({"device": "SoapySDR:" + m.group(1)})
    return found


@register(id="rtlsdr_attune", name="Ether Attunement", glyph="📻", min_level=1,
          psyche_cost=5, xp=12, school="Divination",
          desc="Attune to any attached SDR (RTL-SDR, HackRF, USRP, Airspy, Soapy) "
               "and feel the noise floor. Receive-only probe; simulates if none found.")
def _attune(engine) -> Dict[str, Any]:
    sdrs = detect_sdrs()
    if sdrs:
        names = ", ".join(s["device"] for s in sdrs)
        summary = f"I feel the ether through: {names}."
        return {"summary": summary, "items": sdrs, "count": len(sdrs)}
    summary = "No crystal attached — I imagine the 915 MHz hum. (simulated)"
    items = [{"device": "RTL-SDR Blog V4 (sim)", "tuner": "R828D",
              "noise_floor_dbm": -random.randint(95, 115)}]
    return {"summary": summary, "items": items, "count": len(items)}


# --------------------------------------------------------------------------- #
# US Sub-GHz Sweep — listen to ISM broadcasts via rtl_433 (RX only)
# --------------------------------------------------------------------------- #
@register(id="subghz_listen", name="Sub-GHz Whisper", glyph="🛰", min_level=3,
          psyche_cost=12, xp=20, school="Divination",
          desc="Listen to the public ISM bands (315/433.92/915 MHz) — weather "
               "stations, sensors, telemetry. Decodes only; never transmits.")
def _subghz(engine) -> Dict[str, Any]:
    heard: List[Dict[str, Any]] = []
    if _have("rtl_433"):
        raw = _run(["rtl_433", "-F", "csv", "-T", "6"], timeout=10)
        for line in raw.splitlines():
            if "," in line and not line.lower().startswith("time"):
                parts = line.split(",")
                heard.append({"model": parts[2] if len(parts) > 2 else "device",
                              "band": "433.92MHz"})
    if not heard:
        models = ["Acurite-Tower", "LaCrosse-TX", "Oregon-THGR", "TPMS-Toyota",
                  "Nexus-TH", "Fineoffset-WH2", "Honeywell-Door"]
        bands = ["315MHz", "433.92MHz", "915MHz"]
        for nm in random.sample(models, random.randint(2, 5)):
            heard.append({"model": nm, "band": random.choice(bands), "sim": True})
    with engine._lock:
        engine.pet.networks_sensed += len(heard)
    engine._award(2 + len(heard))
    summary = f"I hear {len(heard)} voices murmuring in the sub-gigahertz dark."
    return {"summary": summary, "items": heard, "count": len(heard)}


# --------------------------------------------------------------------------- #
# LoRa Mesh Whisper — read local Meshtastic logs (file read only)
# --------------------------------------------------------------------------- #
@register(id="lora_whisper", name="LoRa Mesh Whisper", glyph="🌐", min_level=4,
          psyche_cost=10, xp=18, school="Divination",
          desc="Read local Meshtastic / LoRa capture logs and count the far "
               "minds in the mesh. Reads files only; no radio output.")
def _lora(engine) -> Dict[str, Any]:
    nodes = set()
    log_dir = os.path.join(engine.home, "lora_logs")
    try:
        if os.path.isdir(log_dir):
            for fn in os.listdir(log_dir):
                if fn.endswith((".json", ".jsonl")):
                    with open(os.path.join(log_dir, fn), "r", errors="ignore") as fh:
                        for line in fh:
                            m = re.search(r'"from"\s*:\s*"?(\w+)"?', line)
                            if m:
                                nodes.add(m.group(1))
    except Exception:
        pass
    sim = False
    if not nodes:
        sim = True
        nodes = {f"!{random.randint(0x10000000, 0xffffffff):08x}"
                 for _ in range(random.randint(2, 6))}
    items = [{"node": n, "sim": sim} for n in list(nodes)[:30]]
    engine._award(2 + len(items))
    summary = f"{len(items)} distant minds echo across the LoRa mesh."
    return {"summary": summary, "items": items, "count": len(items)}


# --------------------------------------------------------------------------- #
# Sky-Mind 1090 — read ADS-B aircraft (public broadcast, RX only)
# --------------------------------------------------------------------------- #
@register(id="adsb_sky", name="Sky-Mind 1090", glyph="✈", min_level=5,
          psyche_cost=14, xp=24, school="Divination",
          desc="Read aircraft transponders overhead (ADS-B 1090 MHz) from a "
               "local dump1090 feed. Listens to public broadcasts only.")
def _adsb(engine) -> Dict[str, Any]:
    planes: List[Dict[str, Any]] = []
    for path in ("/run/dump1090-fa/aircraft.json",
                 "/run/dump1090/aircraft.json",
                 os.path.join(engine.home, "aircraft.json")):
        if os.path.exists(path):
            try:
                import json
                with open(path) as fh:
                    data = json.load(fh)
                for a in data.get("aircraft", [])[:30]:
                    planes.append({"flight": (a.get("flight") or a.get("hex") or "?").strip(),
                                   "alt": a.get("alt_baro", "?")})
            except Exception:
                pass
            break
    if not planes:
        for _ in range(random.randint(2, 6)):
            planes.append({"flight": f"{random.choice(['UAL','DAL','SWA','FDX'])}"
                           f"{random.randint(100,9999)}",
                           "alt": random.choice([31000, 35000, 38000, 12000]),
                           "sim": True})
    engine._award(2 + len(planes))
    summary = f"I touch {len(planes)} minds soaring in the sky above."
    return {"summary": summary, "items": planes, "count": len(planes)}
